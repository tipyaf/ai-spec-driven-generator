# Stack Profile: PostgreSQL + TimescaleDB

## Database Engine

- PostgreSQL 16
- TimescaleDB extension for time-series tables
- Alembic for schema migrations
- SQLAlchemy 2.x ORM (async) for application-level access
- Named schemas (e.g. `auth`, `trading`) to namespace tables by domain

---

## Security ACs (auto-added to every database story by Story Refiner)

These AC-SEC items are added automatically to every story that touches a database migration,
ORM model, or DB-layer service function. Edit only if the project requires a specific override.

- [ ] AC-SEC-01: No raw SQL string interpolation -- use parameterized queries or ORM | verify: grep -rn "f\"SELECT\|f'SELECT\|% (" app/services/ (must return no matches for user-controlled values)
- [ ] AC-SEC-02: User-facing IDs are not sequential integers that allow enumeration -- use UUIDs or opaque tokens | verify: static -- read new table migration, confirm primary key type is UUID or equivalent
- [ ] AC-SEC-03: Sensitive columns (password_hash, api_key, secret) never returned by default SELECT * | verify: static -- read ORM model, confirm sensitive columns are excluded from default response schemas

---

## Best Practice ACs (auto-added by Story Refiner)

These AC-BP items are added automatically to every story that touches a database migration,
ORM model, or DB-layer service function. Edit only if the project has an explicit override in CLAUDE.md.

- [ ] AC-BP-01: Every new table has a migration with upgrade() and downgrade() | verify: static -- read migration file, confirm both upgrade() and downgrade() are implemented (downgrade must not be `pass`)
- [ ] AC-BP-02: Indexes added for all FK columns and frequently-queried columns | verify: static -- read migration file, confirm `op.create_index()` calls for FK columns and query-hot columns
- [ ] AC-BP-03: CHECK constraints used for status/type enums (not application-level only) | verify: static -- read migration upgrade(), confirm `sa.CheckConstraint()` for enum-like columns
- [ ] AC-BP-04: TimescaleDB hypertables created for time-series tables | verify: grep -n "create_hypertable" alembic/versions/<migration>.py

---

## Forbidden Patterns

| Pattern | Why forbidden |
|---------|--------------|
| Sequential integer PKs on user-facing resources | Allows enumeration attacks (guess IDs to scrape data) |
| Raw string interpolation in SQL (`f"WHERE id = {user_id}"`) | SQL injection vector |
| `SELECT *` in application queries | Returns extra columns, breaks if schema changes, exposes sensitive data |
| Migrations with empty `downgrade()` (`pass`) | Cannot roll back -- makes hotfix deploys impossible |
| Missing FK indexes | Full table scans on every JOIN; degrades performance at scale |
| Enum values enforced only in application code | DB can accept invalid values if written directly or via another client |
| `timestamp without time zone` for event times | Ambiguous across timezones; always use `timestamptz` |
| Storing JSON blobs for structured data that needs querying | Cannot index efficiently; should be normalized columns |

---

## Naming Conventions

| What | Convention | Example |
|------|-----------|---------|
| Schemas | `snake_case` | `auth`, `trading` |
| Tables | `snake_case` (plural) | `exchange_configs`, `refresh_tokens` |
| Columns | `snake_case` | `created_at`, `user_id` |
| Primary keys | `id` (UUID type) | `id UUID DEFAULT gen_random_uuid()` |
| Foreign keys | `<table_singular>_id` | `user_id`, `exchange_config_id` |
| Indexes | `ix_<table>_<column>` | `ix_exchange_configs_user_id` |
| Constraints | `ck_<table>_<column>` | `ck_bots_status` |
| Migration files | Alembic auto-generated with descriptive message | `20260315_add_exchange_configs.py` |

---

## Migration Patterns

### Canonical upgrade/downgrade

```python
def upgrade() -> None:
    op.create_table(
        "exchange_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exchange", sa.String(50), nullable=False),
        sa.Column("api_key", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE"),
        sa.CheckConstraint("status IN ('active', 'inactive', 'error')",
                           name="ck_exchange_configs_status"),
        schema="trading",
    )
    op.create_index(
        "ix_exchange_configs_user_id", "exchange_configs", ["user_id"], schema="trading"
    )


def downgrade() -> None:
    op.drop_index("ix_exchange_configs_user_id", table_name="exchange_configs",
                  schema="trading")
    op.drop_table("exchange_configs", schema="trading")
```

### TimescaleDB hypertable

```python
def upgrade() -> None:
    op.create_table(
        "ohlcv",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("open", sa.Numeric(18, 8), nullable=False),
        sa.Column("high", sa.Numeric(18, 8), nullable=False),
        sa.Column("low", sa.Numeric(18, 8), nullable=False),
        sa.Column("close", sa.Numeric(18, 8), nullable=False),
        sa.Column("volume", sa.Numeric(28, 8), nullable=False),
        schema="trading",
    )
    op.execute(
        "SELECT create_hypertable('trading.ohlcv', 'time', if_not_exists => TRUE)"
    )


def downgrade() -> None:
    op.drop_table("ohlcv", schema="trading")
```

---

## Schema Alignment Test (mandatory for ORM model changes)

Every story that adds or modifies an ORM model MUST include a schema alignment test:

```python
async def test_exchange_configs_schema_matches_orm(db_session):
    """Verify ORM model columns match the migrated DB schema."""
    result = await db_session.execute(
        text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'trading'
              AND table_name = 'exchange_configs'
        """)
    )
    db_columns = {row[0] for row in result.fetchall()}

    orm_columns = {c.name for c in ExchangeConfig.__table__.columns}

    assert orm_columns.issubset(db_columns), (
        f"ORM columns missing from DB: {orm_columns - db_columns}"
    )
```

This test catches the case where a column is added to the ORM model but the migration was not updated.

---

## Story Refiner Instructions

When refining a `database` story, the Story Refiner MUST:

1. Read this file before writing any ACs
2. Copy all AC-SEC-* items into the story's `### Security (AC-SEC-*)` section
3. Copy all AC-BP-* items into the story's `### Best Practice (AC-BP-*)` section
4. Substitute `<migration>`, `<table>`, file path placeholders with the actual names for this story
5. Add project-specific overrides AFTER the standard items -- never replace them
6. Add story-specific AC-FUNC-* items in the `### Functional (AC-FUNC-*)` section

For TimescaleDB stories: always include AC-BP-04 and ensure the `create_hypertable` call
is present in the migration's upgrade() function.

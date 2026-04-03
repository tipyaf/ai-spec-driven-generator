# Builder — Migration Agent — Reference

> This file contains templates and examples. Load only when needed.

---

## Migration Template (Alembic)

```python
"""Add portfolios table

Revision ID: abc123def456
Revises: prev_revision_id
Create Date: 2026-04-04 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "abc123def456"
down_revision = "prev_revision_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "portfolios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        # Foreign keys
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        # Indexes
        sa.Index("ix_portfolios_user_id", "user_id"),
        schema="public",
    )


def downgrade() -> None:
    op.drop_table("portfolios", schema="public")
```

### Add Column Migration
```python
def upgrade() -> None:
    op.add_column("portfolios", sa.Column("is_active", sa.Boolean(),
                  server_default=sa.text("true"), nullable=False))


def downgrade() -> None:
    op.drop_column("portfolios", "is_active")
```

### Rename Column Migration (manual)
```python
def upgrade() -> None:
    op.alter_column("portfolios", "name", new_column_name="title")


def downgrade() -> None:
    op.alter_column("portfolios", "title", new_column_name="name")
```

### Add Constraint Migration (manual)
```python
def upgrade() -> None:
    op.create_check_constraint(
        "ck_portfolios_status",
        "portfolios",
        "status IN ('active', 'paused', 'archived')",
    )
    op.create_unique_constraint(
        "uq_portfolios_user_name",
        "portfolios",
        ["user_id", "name"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_portfolios_user_name", "portfolios", type_="unique")
    op.drop_constraint("ck_portfolios_status", "portfolios", type_="check")
```

---

## Schema Alignment Test Template

```python
import pytest
from sqlalchemy import inspect
from app.models.portfolio import Portfolio


@pytest.mark.usefixtures("apply_migrations")
class TestSchemaAlignment:
    """Verify ORM model columns exist in the actual database after migration."""

    def test_portfolios_table_columns(self, db_engine):
        inspector = inspect(db_engine)
        db_columns = {col["name"] for col in inspector.get_columns("portfolios")}

        # Every ORM column must exist in the DB
        orm_columns = {col.name for col in Portfolio.__table__.columns}
        missing = orm_columns - db_columns
        assert missing == set(), f"ORM columns missing from DB: {missing}"

    def test_portfolios_indexes(self, db_engine):
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("portfolios")
        index_columns = {tuple(idx["column_names"]) for idx in indexes}

        # FK indexes are mandatory (AC-BP)
        assert ("user_id",) in index_columns, "Missing index on user_id FK"

    def test_portfolios_foreign_keys(self, db_engine):
        inspector = inspect(db_engine)
        fks = inspector.get_foreign_keys("portfolios")
        fk_targets = {(fk["referred_table"], tuple(fk["referred_columns"])) for fk in fks}

        assert ("users", ("id",)) in fk_targets, "Missing FK to users.id"
```

---

## Migration Roundtrip Test Template

```python
import subprocess


def test_migration_roundtrip():
    """Upgrade -> downgrade -> upgrade must all complete without error."""
    # Upgrade to head
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Upgrade failed: {result.stderr}"

    # Downgrade one revision
    result = subprocess.run(
        ["alembic", "downgrade", "-1"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Downgrade failed: {result.stderr}"

    # Upgrade again
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Re-upgrade failed: {result.stderr}"
```

---

## Constraint Test Template

```python
import pytest
from sqlalchemy.exc import IntegrityError


class TestPortfolioConstraints:

    def test_name_not_null(self, db_session):
        """NOT NULL on name column is enforced."""
        with pytest.raises(IntegrityError):
            db_session.execute(
                text("INSERT INTO portfolios (id, user_id) VALUES (gen_random_uuid(), :uid)"),
                {"uid": test_user_id},
            )
            db_session.commit()

    def test_status_check_constraint(self, db_session):
        """CHECK constraint rejects invalid status."""
        with pytest.raises(IntegrityError):
            db_session.execute(
                text("UPDATE portfolios SET status = 'invalid' WHERE id = :id"),
                {"id": portfolio_id},
            )
            db_session.commit()

    def test_unique_user_name(self, db_session, portfolio_factory):
        """UNIQUE(user_id, name) prevents duplicates."""
        portfolio_factory(user_id=user_id, name="Same Name")
        with pytest.raises(IntegrityError):
            portfolio_factory(user_id=user_id, name="Same Name")
            db_session.commit()

    def test_fk_cascade_delete(self, db_session):
        """FK ON DELETE CASCADE removes portfolios when user is deleted."""
        db_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        db_session.commit()
        result = db_session.execute(
            text("SELECT count(*) FROM portfolios WHERE user_id = :uid"),
            {"uid": user_id},
        )
        assert result.scalar() == 0
```

---

## Migration Conflict Resolution Checklist

- [ ] Identify all current heads: `alembic heads`
- [ ] Determine which branches conflict
- [ ] Create merge migration: `alembic merge heads -m "merge [branch_a] and [branch_b]"`
- [ ] If same table modified in both branches: manually order operations
- [ ] Apply and verify single head: `alembic current`
- [ ] Run roundtrip test

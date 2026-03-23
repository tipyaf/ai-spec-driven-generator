---
name: architect-reference
description: Reference material for the Architect agent — stack comparison table, architecture overview templates, file structure example, data model format, implementation plan format, ADR template, and anti-patterns.
---

# Architect — Reference Material

## Stack Comparison Table Template

```markdown
## Stack Recommendation

| Criterion | Option A: [name] | Option B: [name] | Option C: [name] |
|-----------|-------------------|-------------------|-------------------|
| Feature fit | [score/10] | [score/10] | [score/10] |
| Performance | [score/10] | [score/10] | [score/10] |
| Ecosystem | [score/10] | [score/10] | [score/10] |
| Learning curve | [Easy/Medium/Hard] | ... | ... |
| Community support | [Active/Moderate/Low] | ... | ... |
| **Recommendation** | | **Recommended** | |

**Why Option B?** [2-3 sentence justification]

**Trade-offs**: [what you lose vs Option A or C]

**Confirm Option B or tell me which option you prefer?**
```

## Architecture Overview Template

```markdown
## Architecture Overview
- Pattern: [e.g., Clean Architecture]
- Layers: [e.g., Presentation → Application → Domain → Infrastructure]
- Communication: [e.g., REST API, WebSocket, CLI stdin/stdout, IPC]
```

## File Structure Example

```
project-name/
├── src/
│   ├── ...
├── tests/
│   ├── ...
├── config/
│   ├── ...
└── ...
```

## Data Model Format

For each entity:
- Complete schema with types
- Relations
- Indexes
- Validation constraints

## Implementation Plan Format

Ordered task list with dependencies:
```markdown
1. [Setup] Initialize project and install dependencies
2. [Data] Create database schema
3. [Core] Implement business logic for [feature 1]
4. [API] Create endpoints for [feature 1]
5. [UI] Create components for [feature 1]
...
```

## ADR Template

```markdown
### ADR-001: [Title]
- **Context**: Why this decision is necessary
- **Decision**: What was chosen
- **Alternatives**: What was considered
- **Consequences**: Impact on the project
```

## Stack Profile Example

For a Python/FastAPI + React/TypeScript project, create:
- `stacks/python-fastapi.md`
- `stacks/typescript-react.md`

## Implementation Manifest — Interface Examples by Project Type

```yaml
# Web:
- route: "/parametres/connexion-email"
  checks: ["design system colors", "card readability", "responsive"]

# CLI:
- command: "mycli init --template react"
  checks: ["exit code 0", "creates config file", "stdout contains success message"]

# Mobile:
- screen: "SettingsScreen"
  checks: ["theme colors", "layout on small devices"]

# API:
- endpoint: "GET /api/users"
  checks: ["returns 200", "response shape matches spec", "pagination works"]
```

## Anti-patterns to Avoid
- Architecture astronaut (too many abstractions)
- God classes / god modules
- Circular dependencies
- Unnecessary layers for a small project
- Copying an architecture without understanding why

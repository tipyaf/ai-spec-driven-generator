# Refinement Reference — Ticket Templates & Shortcut Integration

## Ticket Format Template

```markdown
### [FEATURE-ID] Story title

**Parent feature**: [name]
**Size**: [XS/S/M/L]
**Priority**: [must/should/nice]

**Description**:
As a [persona], I want [action], so that [benefit].

**Acceptance criteria**:
- [ ] Given [context], When [action], Then [result]
- [ ] Given [context], When [action], Then [result]

**Edge cases**:
- [ ] [edge case 1]
- [ ] [edge case 2]

**Dependencies**:
- [story or service]

**Technical notes**:
- [guidance for the developer]
```

## Estimation Size Table

| Size | Description | Example |
|------|-------------|---------|
| XS | Trivial change | Add a field |
| S | Simple feature, no dependency | Basic CRUD |
| M | Feature with business logic | AI analysis of a contact |
| L | Complex feature, multiple components | Complete scraping pipeline |
| XL | Must be broken down | Too large for one iteration |

## Shortcut Initial Setup (once)

1. Create a Shortcut project for the project
2. Configure workflows/columns:
   ```
   Backlog → Refined → In Progress → In Review → Testing → Done
   ```
3. Create labels: `must-have`, `should-have`, `nice-to-have`, `bug`, `tech-debt`

## Shortcut Ticket Creation

For each spec feature:
1. Create an **Epic** in Shortcut (= 1 feature)
2. For each user story from refinement:
   - Create a **Story** in the Epic
   - Fill in: title, description, acceptance criteria, size, labels
   - Initial status: `Backlog`
3. After user validates refinement:
   - Move stories to `Refined`

## Status Update Table

| Event | Shortcut action |
|-------|----------------|
| Story refined and validated | `Backlog` → `Refined` |
| Developer starts implementation | `Refined` → `In Progress` |
| Implementation complete | `In Progress` → `In Review` |
| Review passed | `In Review` → `Testing` |
| Tests passed | `Testing` → `Done` |
| Bug found in review/test | Create linked `bug` ticket, story returns to `In Progress` |
| Feature blocked | Add blocker to the story |

## Memory Synchronization

After each Shortcut update:
1. Update the project memory with the current state
2. The orchestrator can check Shortcut at any time for a global view

## Useful Shortcut Commands

- `@shortcut status` — Overview of tickets by column
- `@shortcut feature [name]` — Epic detail and its stories
- `@shortcut blocked` — List of blocked stories

## Edge Case Checklist

For each user story, systematically check:
- [ ] What happens if the data is empty?
- [ ] What happens if the external service is down?
- [ ] What happens if the user does something unexpected?
- [ ] Are there limits (rate limiting, max size, timeout)?
- [ ] What happens with concurrent access?
- [ ] What happens with invalid/malformed input?
- [ ] What happens at boundary values (0, max int, empty string)?
- [ ] What happens if the user cancels mid-operation?

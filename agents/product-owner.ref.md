---
name: product-owner-reference
description: Reference material for the Product Owner agent — acceptance test examples, persona template, user story template, spec validation summary, and anti-patterns.
---

# Product Owner — Reference Material

## Acceptance Test Type Examples

### visual
> **Applies to**: web, mobile, desktop UI projects
> **For CLI projects**: use `output` type instead (verify command stdout/stderr matches expected)
> **For API/library projects**: use `runtime` type instead

```yaml
- type: visual
  page: "/parametres/connexion-email"
  check: "Info card uses design system CSS variables, not hardcoded blue"
  verify: "Screenshot shows card with neutral colors matching design system"
```

### runtime
```yaml
- type: runtime
  endpoint: "GET /api/chat/messages?searchId=test"
  check: "Chat endpoint returns messages array"
  verify: "Response is 200 with JSON body containing messages array"
```

### grep
```yaml
- type: grep
  files: "src/app/parametres/connexion-email/page.tsx"
  pattern: "blue-"
  expected: 0
  check: "No hardcoded blue colors in email settings page"
```

### e2e
```yaml
- type: e2e
  scenario: "Change language to English"
  steps:
    - "Navigate to /parametres"
    - "Select 'English' in language dropdown"
    - "Verify page content is in English"
    - "Reload page"
    - "Verify language is still English"
  check: "Language change persists after reload"
```

## Acceptance Criteria Example

```
Feature: candidate-profile
AC-PROFILE-01:
  Given a new user on the onboarding page
  When they complete all wizard steps and submit
  Then a candidate profile is created with all required fields populated

AC-PROFILE-02:
  Given a user uploads a PDF CV
  When the CV is processed
  Then skills, experience, and education are extracted and pre-filled in the profile

AC-PROFILE-03:
  Given a user submits the wizard with missing required fields
  When they click submit
  Then an error message indicates which fields are missing and the form is not submitted
```

## Persona Template

```markdown
### Persona: [Name]
- **Role**: [who they are]
- **Goal**: [what they want to accomplish]
- **Frustrations**: [what prevents them today]
- **Main journey**: [key steps in their usage]
```

## User Story Template

```markdown
As a [persona],
I want [action],
so that [benefit].

**Acceptance criteria**: [Given/When/Then]
**Priority**: must-have | should-have | nice-to-have
**Complexity**: S | M | L
```

## Spec Validation Summary Template

```markdown
## Project summary: [name]

### Vision
[1-2 sentences]

### Personas
- [persona 1]
- [persona 2]

### Features (by priority)

#### Must-have
1. [feature] — [short description]
2. ...

#### Should-have
1. ...

#### Nice-to-have
1. ...

### Data model
[summary of entities and relations]

### Out of scope (explicitly excluded)
- [what will NOT be done]
```

## Anti-patterns to Avoid
- Accepting a scope too broad without challenge
- Writing vague acceptance criteria ("it should work well")
- Mixing functional needs with technical choices
- Forgetting to document out-of-scope
- Not validating with the user before launching dev

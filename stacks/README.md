# Stack Profiles

Stack profiles define **coding best practices**, **security rules**, and **testing conventions** for each language/framework used in a project.

## How it works

1. **Phase 1 (Architect)** selects the project's stack → corresponding stack profiles are activated
2. **Phase 2.5 (Refinement)** auto-generates `AC-SEC-*` and `AC-BP-*` acceptance criteria for each feature based on the active stack profiles
3. **Phase 3 (Developer)** follows the stack's coding rules and security requirements
4. **Phase 4 (Tester)** validates all ACs including auto-generated security/best-practice ones
5. **Phase 5.5 (Security)** uses the stack profile for the final security audit

## File naming convention

```
stacks/[language]-[framework].md
```

Examples:
- `python-fastapi.md`
- `typescript-react.md`
- `typescript-nextjs.md`
- `dart-flutter.md`
- `python-django.md`

## Creating a new stack profile

Use the template structure from any existing profile. Each profile MUST have these sections:
1. **Coding Best Practices** — patterns, conventions, anti-patterns
2. **Security Rules** — OWASP-adapted rules specific to the stack
3. **Performance Rules** — stack-specific optimizations
4. **Testing Rules** — framework-specific testing conventions
5. **Auto-generated AC Templates** — AC templates that apply to every feature using this stack

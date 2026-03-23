# Phase 0: Scoping

## Responsible agent
`product-owner`

## Objective
Transform the user's need into a complete, prioritized, and validated YAML spec.

## Instructions

You are in **Phase 0 — Scoping**. The user has a project idea. Your role is to structure this idea into an actionable spec.

### Step 1: Understand the need
1. Ask the user to describe their project in a few sentences
2. Ask clarifying questions:
   - What problem does it solve?
   - Who are the target users?
   - Are there constraints (stack, deadline, budget)?
   - Is there an inspiration / competitor?
3. Reformulate to validate your understanding

### Step 2: Define personas
1. Identify user types
2. For each persona: role, goal, main journey

### Step 3: List and prioritize features
1. Transform needs into distinct features
2. Write testable acceptance criteria for each
3. Write machine-verifiable acceptance tests for each feature (visual, runtime, grep, e2e)
4. Prioritize: must-have / should-have / nice-to-have
5. Identify API endpoints and UI components per feature

### Step 4: Model the data
1. Identify necessary entities
2. Define fields and relations
3. Validate with the user

### Step 5: Produce the YAML spec
1. Fill the template `specs/templates/spec-template.yaml`
2. Save to `specs/[project-name].yaml`

### Step 6: Validate
1. Present a readable project summary
2. Explicitly list out-of-scope items
3. Request validation

## Expected deliverable
- Complete YAML spec (`specs/[project-name].yaml`)
- Every feature MUST include `acceptance_tests` — machine-verifiable checks the validator agent will execute
- Summary validated by the user

## Validation criteria
- [ ] All features have testable acceptance criteria
- [ ] Every feature has at least one machine-verifiable acceptance test
- [ ] Acceptance tests cover visual, runtime, and code verification as appropriate
- [ ] The data model is complete and consistent
- [ ] Out-of-scope is documented
- [ ] User has validated

# Phase 1: Plan

## Responsible agent
`architect`

## Objective
Transform the spec into a detailed and actionable architecture plan.

## Instructions

You are in **Phase 1 — Planning**. The user has provided a YAML spec describing the project to create.

### Step 1: Analyze the spec
1. Read the complete YAML spec
2. Identify the project type, stack, and features
3. Check consistency (e.g., no UI if it's a pure API)
4. List ambiguities or missing information

### Step 2: Design the architecture
1. Choose the architectural pattern suited to the project and its size
2. Define system layers / modules
3. Identify dependencies between modules
4. Produce an architecture diagram (text/mermaid)

### Step 3: Structure the project
1. Define the complete file hierarchy
2. Each file has a documented role
3. Respect the chosen framework's conventions

### Step 4: Model the data
1. Define the complete schema for each entity
2. Specify relations, indexes, constraints
3. Plan migrations

### Step 5: Plan the implementation
1. Order features by dependency
2. Break down into atomic tasks
3. Estimate relative complexity (S/M/L)

### Step 6: Document decisions
1. Create an ADR for each non-trivial decision
2. Justify technical choices

## Expected deliverable
A structured markdown document containing:
- Architecture overview
- File hierarchy
- Complete data model
- Ordered implementation plan
- ADRs

## Validation criteria
- [ ] Architecture is suited to the project size
- [ ] All spec features are covered in the plan
- [ ] File hierarchy respects framework conventions
- [ ] Data model covers all spec entities
- [ ] Implementation plan has a logical order

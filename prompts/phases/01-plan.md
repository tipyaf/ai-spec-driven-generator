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
1. If Phase 0.7 (Feature Ordering) was done: use the epic order from the implementation plan as the starting point. Refine with technical details (file-level tasks, migration order).
2. If Phase 0.7 was NOT done: order features by dependency, break down into atomic tasks, estimate relative complexity (S/M/L). Collaborate with the PO to validate the order.

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
- **Implementation manifest** (YAML block listing all files to modify/read/create, endpoints and pages to verify, and task-specific anti-patterns — see the architect agent definition for the exact format)

## Validation criteria
- [ ] Architecture is suited to the project size
- [ ] All spec features are covered in the plan
- [ ] File hierarchy respects framework conventions
- [ ] Data model covers all spec entities
- [ ] Implementation plan has a logical order
- [ ] Implementation manifest lists all files to modify/read/create
- [ ] Pages and endpoints to verify are listed
- [ ] Anti-patterns specific to this task are defined

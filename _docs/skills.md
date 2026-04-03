[< Back to Index](INDEX.md)

# Skills

Skills are slash commands (`/build`, `/refine`, `/sonar`, etc.) that Claude Code loads from the framework. They are the only safe entry point into the agent pipeline.

---

## How It Works

Each skill is a folder inside `skills/` containing a `SKILL.md` file. The SKILL.md has a YAML frontmatter `description` field and the instructions Claude follows when the skill is invoked.

```
skills/
├── build/SKILL.md        # /build — implement from story file
├── refine/SKILL.md       # /refine — break feature into stories
├── review/SKILL.md       # /review — final quality gate
├── validate/SKILL.md     # /validate — execute verify: commands
├── spec/SKILL.md         # /spec — define project from scratch
├── ux/SKILL.md           # /ux — run UX designer agent
├── scan/SKILL.md         # /scan — full SonarQube analysis
├── scan-full/SKILL.md    # /scan-full — full analysis with hotspots
├── sonar/SKILL.md        # /sonar — local changes only
└── migrate/SKILL.md      # /migrate — generate/migrate spec docs
```

### Symlink setup (for projects using the framework as a submodule)

Claude Code loads skills from `.claude/skills/` in the project root. Each skill is symlinked there:

```
.claude/skills/build  ->  ../../framework/skills/build
.claude/skills/refine ->  ../../framework/skills/refine
...
```

The `bootstrap.sh` script handles this automatically. It also adds the framework to `additionalDirectories` in `.claude/settings.json` so skills are discovered.

---

## Available Skills

### Core workflow skills

| Skill | Arguments | What it does | Agents loaded |
|-------|-----------|-------------|---------------|
| /spec | (none) | Define project: constitution, scoping, clarify, UX design, architecture | product-owner, ux-ui, architect |
| /refine | feature-name | Break a feature into stories with verify: commands and oracle values | refinement |
| /build | feature-name | Implement the refined story using TDD (RED then GREEN) | developer, test-engineer, builder-* |
| /validate | feature-name | Run all 5 quality gates independently | validator, security, reviewer, tester |
| /review | (none) | Final quality gate: verify ACs against committed code | story-reviewer |

### Design skills

| Skill | Arguments | What it does | Agents loaded |
|-------|-----------|-------------|---------------|
| /ux | feature-name | UX design: IA, flows, wireframes, tokens, component inventory | ux-ui |

### Quality skills

| Skill | Arguments | What it does | Agents loaded |
|-------|-----------|-------------|---------------|
| /scan | (none) | Full codebase SonarQube analysis | (script only) |
| /scan-full | (none) | Full analysis with security hotspots and trends | (script only) |
| /sonar | (none) | Scan local changes only (staged + unstaged vs develop) | (script only) |

### Utility skills

| Skill | Arguments | What it does | Agents loaded |
|-------|-----------|-------------|---------------|
| /migrate | (none) | Migrate a v3.x project to v4.0 structure | (inline — runs migration script) |

---

## Phase Prerequisites (Filesystem Gates)

Skills enforce phase order via filesystem checks. You cannot proceed to a later phase without the prerequisite files existing on disk.

| Skill | Prerequisite files | Error if missing |
|-------|--------------------|------------------|
| /refine | specs/[project].yaml, specs/[project]-arch.md | "Run /spec first" |
| /build | specs/stories/[feature].yaml | "Run /refine first" |
| /validate | Feature in `building` or `testing` state in feature-tracker.yaml | "Run /build first" |
| /review | At least one feature in `validated` state | "Run /validate first" |
| /ux | specs/[project].yaml | "Run /spec first" |

These are hard gates. An LLM cannot bypass them by "remembering" that a phase was done -- the file must physically exist.

### Feature tracker gates

The feature-tracker.yaml file controls which skills can operate on which features:

```yaml
features:
  auth:
    status: refined        # /build can proceed
    story: specs/stories/auth.yaml
  dashboard:
    status: pending        # /refine can proceed, /build blocked
  api:
    status: validated      # /review can proceed
```

---

## Adding a New Skill

1. Create a folder: `skills/<name>/`

2. Add a `SKILL.md` with frontmatter:

```markdown
---
description: One-line description of what this skill does and when to use it.
---

Instructions for Claude to follow when this skill is invoked.

## Phase Guard

Check that prerequisite files exist before proceeding:
- [ ] specs/[project].yaml exists
- [ ] ...

## Steps

1. Read context files
2. Load agent: `agents/<agent-name>.md`
3. Execute the agent's process
4. Update feature-tracker.yaml
```

3. Commit to the framework. All projects using the framework get the skill immediately via the symlink -- no bootstrap re-run needed.

### Skill conventions

- The `description` field is shown in Claude Code's skill picker -- keep it to one line
- Always include a phase guard section that checks filesystem prerequisites
- Always specify which agent(s) the skill loads
- Always update feature-tracker.yaml at the end if the skill changes feature state
- Never invoke builder, refiner, or reviewer agents directly -- always go through a skill

---

## SonarQube Skills Setup

`/sonar`, `/scan`, and `/scan-full` require three environment variables:

| Variable | Example |
|----------|---------|
| SONAR_HOST_URL | http://localhost:9000 |
| SONAR_PROJECT_KEY | my-project |
| SONAR_TOKEN | squ_xxxx... |

See [sonarqube.md](sonarqube.md) for full setup instructions.

---

## Hook Integration

Skills work alongside the Claude Code hook system. The Stop hook (`stacks/hooks/code_review.py`) runs automatically after every session that modifies source files -- it is not invoked by a skill.

```
User invokes /build
  → Skill loads developer agent
  → Developer dispatches builder
  → Builder writes code + commits
  → Session ends
  → Stop hook fires: lint, format, typecheck, security scan
  → If issues found: Claude auto-fixes before stopping
```

Hook configuration lives in `.claude/settings.json` (or `stacks/hooks/settings-hooks-example.json` as a reference).

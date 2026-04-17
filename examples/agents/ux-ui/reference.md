# UX/UI Reference — Templates & Examples

## Information Architecture Examples

### Web projects — Sitemap
```markdown
#### Public pages
- `/` — Landing / Home page
- `/login` — Login
- `/register` — Registration

#### Authenticated pages
- `/dashboard` — Main dashboard
- `/settings` — User settings

#### Navigation
- Header: [elements]
- Sidebar: [elements] (if applicable)
- Footer: [elements]
```

### Mobile apps — Screen map
```markdown
- Splash → Onboarding → Home (tab bar)
- Tab 1: [screen] → [detail screen]
- Tab 2: [screen] → [detail screen]
- Settings → [sub-screens]
```

### CLI tools — Command tree
```markdown
- `app <command> [options]`
  - `app init` — Initialize project
  - `app run <target>` — Run target
  - `app config set <key> <value>` — Set config
```

### Desktop apps — Menu structure
```markdown
- File → [actions]
- Edit → [actions]
- View → [panels/windows]
- Main window layout: [zones]
```

## User Flow Template

```markdown
### Flow: [Journey name]
1. The user arrives on [page]
2. They see [main elements]
3. They click on [action]
4. [result / transition]
5. ...

### Special states
- **Empty state**: what is shown when there is no data
- **Loading state**: loading indicator
- **Error state**: error message and recovery action
- **Success state**: action confirmation
```

## Design System Template

### Colors
| Role | Color | On background | Contrast ratio | WCAG AA |
|------|-------|---------------|----------------|---------|
| Primary | #1D4ED8 | #FFFFFF | 8.59 : 1 | Pass |
| Secondary | [hex] | [bg hex] | [ratio] | [status] |
| Background | [hex] | — | — | — |
| Surface | [hex] | [bg hex] | — | — |
| Text | [hex] | [bg hex] | [ratio] | [status] |
| Text Muted | [hex] | [bg hex] | [ratio] | [status] |
| Success | [hex] | [bg hex] | [ratio] | [status] |
| Error | [hex] | [bg hex] | [ratio] | [status] |
| Warning | [hex] | [bg hex] | [ratio] | [status] |

### Typography
| Role | Font | Size | Weight |
|------|------|------|--------|
| H1 | [font] | [size] | [weight] |
| H2 | [font] | [size] | [weight] |
| Body | [font] | [size] | [weight] |
| Small | [font] | [size] | [weight] |

### Spacing
- Base unit: [4px/8px]
- Scale: xs(4) sm(8) md(16) lg(24) xl(32) 2xl(48)

### Border radius
- Small: [e.g., 4px] — inputs, badges
- Medium: [e.g., 8px] — cards, buttons
- Large: [e.g., 16px] — modals, containers
- Full: [9999px] — avatars, pills

### Shadows
- sm: [value] — subtle elements
- md: [value] — cards
- lg: [value] — modals, dropdowns

## Component Spec Template

```markdown
### Component: [Name]

**Role**: [1-line description]

**Textual wireframe**:
┌─────────────────────────────────────┐
│  [Layout description]               │
│  ┌─────────┐  ┌──────────────────┐  │
│  │ Element │  │ Element          │  │
│  └─────────┘  └──────────────────┘  │
│  [Button Label]                     │
└─────────────────────────────────────┘

**Props / Data**:
- `prop1`: type — description
- `prop2`: type — description

**States**:
- Default: [description]
- Hover: [description]
- Active: [description]
- Disabled: [description]
- Loading: [description]
- Error: [description]
- Empty: [description]

**Interactions**:
- Click: [action]
- Keyboard: [shortcuts]

**Responsive** (web/mobile UI only):
- Mobile (< 768px): [adaptation]
- Tablet (768-1024px): [adaptation]
- Desktop (> 1024px): [default layout]

**Accessibility** (web/mobile UI only):
- ARIA role: [role]
- Labels: [labels]
- Focus management: [description]

> For CLI: ensure screen-reader friendly output, --no-color flag, --help for every command.
```

## Page Layout Template

```markdown
### Page: [Name] — `[route]`

**Layout**:
┌──────────────────────────────────────────┐
│ Header / Navbar                          │
├──────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────────────────┐  │
│  │ Sidebar  │  │ Content Area         │  │
│  │          │  │                      │  │
│  └──────────┘  └──────────────────────┘  │
├──────────────────────────────────────────┤
│ Footer (optional)                        │
└──────────────────────────────────────────┘

**Components used**:
- [ComponentA] — position and role
- [ComponentB] — position and role

**Required data**:
- [data 1] — source
- [data 2] — source
```

## Anti-Patterns

- Designing without considering empty/error/loading states
- Ignoring mobile
- Too many colors or typographic variations
- Inconsistent navigation between pages
- Forgetting keyboard accessibility
- Using non-standard UI patterns without justification
- Specifying colors without verifying contrast ratios
- Using grey text on grey background (common failure: muted text on light surface)

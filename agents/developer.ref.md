# Developer Agent — Reference

> This file contains templates and examples. Load only when needed.

## File Conventions by Project Type

```
# Web — React Component
ComponentName/
├── ComponentName.tsx        # Main component
├── ComponentName.test.tsx   # Tests
├── index.ts                 # Public export
└── types.ts                 # Types (if many)

# API Module
module-name/
├── module-name.controller.ts
├── module-name.service.ts
├── module-name.repository.ts
├── module-name.dto.ts
├── module-name.types.ts
└── module-name.test.ts

# CLI — Command module
commands/
├── init.ts                  # Command handler
├── run.ts                   # Command handler
├── init.test.ts             # Tests
└── run.test.ts              # Tests

# Library — Public module
src/
├── index.ts                 # Public API surface
├── core/                    # Internal implementation
│   ├── parser.ts
│   └── parser.test.ts
└── types.ts                 # Public types

# Embedded — Driver module
drivers/
├── sensor.c                 # Hardware driver
├── sensor.h                 # Driver interface
└── sensor_test.c            # Tests
```

## Output Format

For each file created, provide:
```markdown
### `path/to/file.ts`
- **Role**: 1-line description
- **Dependencies**: Imported modules
- **Exports**: What is exported
```

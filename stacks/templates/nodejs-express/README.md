# Stack Profile: Node.js + Express (NEW in v5)

## Language & Framework

- Node.js 18+ LTS
- Express 4.x or 5.x
- TypeScript strongly recommended (profile assumes TS; plain JS works too)
- Jest (default) or Vitest for tests
- supertest for HTTP-level integration tests
- zod / joi / express-validator for request validation
- pino or winston for structured logging

See `profile.yaml` for the authoritative build/test/lint commands and forbidden
patterns. See `ac-templates.yaml` for ACs auto-injected by the refinement agent.
See `smoke-boot.yaml` for the G4.1 boot strategy.

---

## Security ACs

Auto-added to every story touching an Express route, middleware, or server entrypoint.
See `ac-templates.yaml` for the authoritative list. Summary:

- `AC-SEC-CORS-ALLOWLIST` — explicit CORS allowlist, never `cors()` defaults
- `AC-SEC-HELMET` — helmet() middleware registered
- `AC-SEC-INPUT-VALIDATION` — zod/joi/express-validator on every request body
- `AC-SEC-NO-SHELL-EXEC-TEMPLATE` — no `exec()` with template-string user input
- `AC-SEC-ERROR-HANDLER` — central error middleware, generic messages, contextual logs

---

## Best Practice ACs

- `AC-BP-ENDPOINT-ASYNC` — I/O handlers are async/await
- `AC-BP-STRUCTURED-LOGGER` — pino/winston with correlation IDs
- `AC-BP-SUPERTEST` — integration tests via supertest
- `AC-BP-TYPING` — `tsc --noEmit` passes in strict mode
- `AC-BP-GRACEFUL-SHUTDOWN` — SIGTERM/SIGINT close connections cleanly

---

## Forbidden Patterns

See `profile.yaml: forbidden_patterns`. Notable:

| Pattern | Why forbidden |
|---------|--------------|
| `app.use(cors())` | Allows all origins — must be an explicit allowlist |
| `res.send(req.query/body/...)` | Echoes user input unsanitized — XSS vector |
| `eval(...)` | Arbitrary code execution |
| `child_process.exec(\`...${userInput}\`)` | Shell command injection — use `execFile` with argv |
| `console.log(...)` in production code | Use a structured logger |

---

## Naming Conventions

| What | Convention | Example |
|------|-----------|---------|
| Files | `kebab-case.ts` | `user-routes.ts` |
| Routes | `/kebab-case/:id` | `/user-accounts/:id` |
| Controller/handler exports | `camelCase` | `createUser`, `listUsers` |
| Types / interfaces | `PascalCase` | `CreateUserDto`, `UserRow` |
| Test files | `*.test.ts` | `user-routes.test.ts` |

---

## Test Patterns

### Supertest canonical setup

```typescript
import request from "supertest";
import { createApp } from "../src/app";

describe("POST /users", () => {
  const app = createApp();

  it("returns 201 with created user", async () => {
    const res = await request(app)
      .post("/users")
      .send({ email: "a@b.com", name: "Ada" })
      .expect(201);
    expect(res.body).toMatchObject({ email: "a@b.com" });
  });

  it("returns 400 when body is invalid", async () => {
    await request(app)
      .post("/users")
      .send({ email: "nope" })
      .expect(400);
  });
});
```

### Middleware error propagation

```typescript
// WRONG: sync throw in async handler is not caught by Express 4
app.get("/x", async (req, res) => { throw new Error("boom"); });

// RIGHT: wrap with asyncHandler or use Express 5 (native promise support)
app.get("/x", asyncHandler(async (req, res) => { throw new Error("boom"); }));
```

---

## Smoke Boot (G4.1)

See `smoke-boot.yaml`. Default: `node dist/server.js` on port 3000 with
`GET /health` returning 200 within 30s.

Projects without a `/health` route should either add one (recommended) or
override `healthcheck.url` in `_work/stacks/registry.yaml`.

---

## Story Refiner Instructions

When refining a story targeting nodejs-express, the Story Refiner MUST:

1. Read `ac-templates.yaml` and inject all `ac_sec` + `ac_bp` items whose
   `applies_to:` matches the story components (endpoint, middleware, server, …).
2. Substitute `<route>`, `<middleware>`, `<handler>` placeholders with actual file names.
3. Add project-specific overrides AFTER the standard items — never replace them.
4. Add story-specific AC-FUNC-* items in the `### Functional (AC-FUNC-*)` section.

The Validator will execute each `verify:` command literally.

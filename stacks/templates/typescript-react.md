# Stack Profile: TypeScript + React

## Language & Framework

- TypeScript 5.x (strict mode)
- React 18 with functional components and hooks
- Vite for build tooling
- React Query (TanStack Query) for data fetching
- React Router v6 for navigation
- Vitest + Testing Library for unit/component tests
- MSW (Mock Service Worker) for API mocking in tests

---

## Security ACs (auto-added to every frontend story by Story Refiner)

These AC-SEC items are added automatically to every story that touches a frontend component
or data-fetching hook. Edit only if the project requires a specific override.

- [ ] AC-SEC-01: No credentials or tokens stored in localStorage -- use HttpOnly cookies or memory only | verify: grep -rn "localStorage.set\|localStorage\[" src/ (must return no matches for auth tokens)
- [ ] AC-SEC-02: All user-supplied content rendered via React JSX (not dangerouslySetInnerHTML) | verify: grep -rn "dangerouslySetInnerHTML" src/ (must return no matches, or each match has a documented exception)
- [ ] AC-SEC-03: API base URL comes from environment variable, not hardcoded | verify: grep -rn "http://\|https://" src/api/ (must not contain hardcoded host URLs)
- [ ] AC-SEC-04: No console.log statements that expose user data or tokens in production code | verify: grep -rn "console\.log" src/ (must return no matches in non-test files, or matches are clearly debug-only)

---

## Best Practice ACs (auto-added by Story Refiner)

These AC-BP items are added automatically to every story that touches a frontend component
or data-fetching hook. Edit only if the project has an explicit override in CLAUDE.md.

- [ ] AC-BP-01: No `any` type without a comment explaining why | verify: grep -rn ": any\b" src/ (each match must have a `// reason:` comment on the same or previous line)
- [ ] AC-BP-02: All data-fetching components handle loading and error states | verify: static -- read component file, confirm loading skeleton/spinner and error boundary or inline error message
- [ ] AC-BP-03: All interactive elements have aria-label or visible text | verify: static -- read JSX output, check buttons/inputs/links for aria-label or text content
- [ ] AC-BP-04: useQuery/useMutation hooks tested with MSW (mock service worker) | verify: grep -rn "msw\|setupServer\|rest\." src/<component>.test.tsx
- [ ] AC-BP-05: No source-file assertions in tests (no fs.readFileSync) | verify: grep -rn "readFileSync\|existsSync" src/ (must return no matches in test files)

---

## Forbidden Patterns

| Pattern | Why forbidden |
|---------|--------------|
| `localStorage.setItem("token", ...)` | Tokens in localStorage are accessible to XSS attacks |
| `dangerouslySetInnerHTML={{ __html: userInput }}` | XSS vector -- always use JSX rendering |
| Hardcoded API URLs (`"http://api.example.com/..."`) | Breaks in different environments; use `import.meta.env.VITE_API_URL` |
| `const x: any = ...` without comment | Silent type safety bypass |
| `fs.readFileSync(...)` in test files | Tests code shape, not behavior -- catches nothing |
| `useEffect` with no cleanup for subscriptions | Memory leaks in long-running sessions |
| Direct DOM manipulation (`document.getElementById`) | Bypasses React's reconciler; causes subtle bugs |
| `@ts-ignore` without explanation comment | Hides type errors that will surface at runtime |
| Fetching data in `useEffect` without React Query | Bypasses cache, loading/error handling, retry logic |

---

## Naming Conventions

| What | Convention | Example |
|------|-----------|---------|
| Component files | `PascalCase.tsx` | `FeatureList.tsx` |
| Hook files | `use<Name>.ts` | `useFeatureList.ts` |
| API module files | `<resource>Api.ts` | `featureApi.ts` |
| Test files | `<Component>.test.tsx` | `FeatureList.test.tsx` |
| CSS module files | `<Component>.module.css` | `FeatureList.module.css` |
| Types/interfaces | `PascalCase` | `Feature`, `FeatureListResponse` |
| Enum values | `SCREAMING_SNAKE_CASE` | `FeatureStatus.ACTIVE` |
| Event handlers | `handle<Action>` | `handleCreate`, `handleDelete` |
| Query keys | `["resource", id]` | `["features", featureId]` |

---

## Test Patterns

### Component test with MSW (canonical)

```typescript
import { render, screen, waitFor } from "@testing-library/react";
import { server } from "../test/server"; // MSW server
import { rest } from "msw";
import { FeatureList } from "./FeatureList";

test("shows features after loading", async () => {
  server.use(
    rest.get("/api/v1/features", (req, res, ctx) =>
      res(ctx.json([{ id: "1", name: "Test Feature", status: "active" }]))
    )
  );

  render(<FeatureList />);

  expect(screen.getByRole("progressbar")).toBeInTheDocument(); // loading state
  await waitFor(() =>
    expect(screen.getByText("Test Feature")).toBeInTheDocument()
  );
});

test("shows error state when API fails", async () => {
  server.use(
    rest.get("/api/v1/features", (req, res, ctx) =>
      res(ctx.status(500), ctx.json({ message: "Internal server error" }))
    )
  );

  render(<FeatureList />);
  await waitFor(() =>
    expect(screen.getByRole("alert")).toBeInTheDocument() // error state
  );
});
```

### Hook test with MSW

```typescript
import { renderHook, waitFor } from "@testing-library/react";
import { server } from "../test/server";
import { rest } from "msw";
import { useFeatureList } from "./useFeatureList";
import { QueryClientWrapper } from "../test/QueryClientWrapper";

test("returns features on success", async () => {
  server.use(
    rest.get("/api/v1/features", (req, res, ctx) =>
      res(ctx.json([{ id: "1", name: "Test Feature" }]))
    )
  );

  const { result } = renderHook(() => useFeatureList(), {
    wrapper: QueryClientWrapper,
  });

  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data).toHaveLength(1);
});
```

---

## Accessibility Checklist

Every new component must satisfy these before the story can pass review:

| Element type | Required attribute(s) |
|-------------|----------------------|
| `<button>` (icon-only) | `aria-label="<action>"` |
| `<input>` | `<label>` element with `for` attr, or `aria-label` |
| `<img>` | `alt="<description>"` (empty string for decorative) |
| Modal/Dialog | `role="dialog"`, `aria-labelledby`, focus trap on open |
| Loading spinner | `role="status"`, `aria-label="Loading"` |
| Error message | `role="alert"` |
| Tab group | `role="tablist"`, `role="tab"`, `aria-selected` |
| Navigation | `<nav>` with `aria-label` |

Color alone must not convey meaning -- always pair color with text or icon.
Minimum contrast ratio: 4.5:1 for normal text, 3:1 for large text (WCAG 2.1 AA).

---

## Story Refiner Instructions

When refining a `frontend` story, the Story Refiner MUST:

1. Read this file before writing any ACs
2. Copy all AC-SEC-* items into the story's `### Security (AC-SEC-*)` section
3. Copy all AC-BP-* items into the story's `### Best Practice (AC-BP-*)` section
4. Substitute `<component>`, `<hook>`, file path placeholders with the actual names for this story
5. Add project-specific overrides AFTER the standard items -- never replace them
6. Add story-specific AC-FUNC-* items in the `### Functional (AC-FUNC-*)` section

The Validator will execute each `verify:` command literally. Ensure grep patterns
and file paths match the actual filenames used in this story.

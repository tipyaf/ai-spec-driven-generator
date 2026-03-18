# Stack Profile: TypeScript + React

## Coding Best Practices

### Project structure
- Feature-based folder structure (`features/[name]/components|hooks|services|types`)
- Shared components in `components/ui/` (design system) and `components/common/`
- Custom hooks in `hooks/` for reusable logic
- API calls in `services/` — never call APIs directly from components
- Types in `types/` or colocated `types.ts` per feature

### Conventions
- **Functional components only** — no class components
- **Named exports** — no default exports (except pages if required by framework)
- Props defined as `interface [Component]Props {}` — not inline
- Use `const` for component definitions: `const MyComponent: FC<Props> = () => {}`
- Destructure props in the function signature
- One component per file — file name matches component name
- Use `index.ts` barrel files for public exports from features

### State management
- Local state: `useState` / `useReducer`
- Server state: React Query (`@tanstack/react-query`) — no manual fetch/useEffect
- Global state: Context API for small apps, Zustand for complex state
- Never store derived data in state — compute it

### Anti-patterns
- Never use `any` — use `unknown` if type is truly unknown, then narrow it
- Never use `useEffect` for data fetching — use React Query
- Never use `index` as key in lists with dynamic order
- Never mutate state directly — always create new references
- Never use inline styles for reusable components — use the design system
- No prop drilling beyond 2 levels — use Context or composition

## Security Rules

### XSS Prevention (OWASP A03)
- React escapes by default — NEVER use `dangerouslySetInnerHTML` unless content is sanitized with DOMPurify
- Sanitize all user-generated content before rendering
- Never interpolate user input into `href`, `src`, or `style` attributes without validation
- URL validation: check protocol is `http:` or `https:` before rendering links

### Authentication (OWASP A07)
- Store JWT tokens in httpOnly cookies — NEVER in localStorage
- Implement CSRF protection if using cookies
- Auto-redirect to login on 401 responses (via Axios/fetch interceptor)
- Clear all auth state on logout (tokens, cached data, user state)

### Data exposure (OWASP A01)
- Never log sensitive data to console in production
- Strip `console.log` in production builds
- Never include secrets or API keys in client-side code
- Use environment variables prefixed with `VITE_` / `NEXT_PUBLIC_` only for public config

### Dependencies
- Keep dependencies updated — run `npm audit` regularly
- No dependencies with known CVEs
- Validate all external data (API responses) at the boundary with Zod or similar

### Content Security Policy
- Configure CSP headers to prevent inline scripts and unauthorized sources
- Use nonce-based CSP for inline scripts if needed

## Performance Rules
- Use `React.memo` only when profiling shows unnecessary re-renders
- Use `useMemo` / `useCallback` for expensive computations and stable references
- Lazy load routes with `React.lazy` + `Suspense`
- Images: use lazy loading, WebP format, proper sizing
- Bundle analysis: keep initial bundle under 200KB gzipped
- Use virtualization (e.g., `react-virtual`) for long lists (100+ items)

## Testing Rules
- Framework: **Vitest** + **React Testing Library**
- Test behavior, not implementation — query by role/text, not by class/id
- Use `userEvent` (not `fireEvent`) for user interactions
- Mock API calls with **MSW** (Mock Service Worker)
- Snapshot tests only for design system components
- Coverage target: 80%+ on business logic, 60%+ on components

## Auto-generated AC Templates

These ACs are automatically added to EVERY feature that has UI components:

```
AC-SEC-[FEATURE]-XSS:
  Given any component in [feature] that renders user-provided data
  When the data contains HTML or script tags
  Then the content is safely escaped or sanitized (no XSS possible)

AC-SEC-[FEATURE]-AUTH-UI:
  Given a protected page/component in [feature]
  When a user is not authenticated
  Then they are redirected to the login page with no flash of protected content

AC-BP-[FEATURE]-TYPES:
  Given all components and hooks in [feature]
  When reviewing the code
  Then no 'any' type is used, all props have typed interfaces, and API responses are validated

AC-BP-[FEATURE]-LOADING:
  Given any component in [feature] that loads async data
  When data is loading
  Then a loading state is displayed (skeleton/spinner)

AC-BP-[FEATURE]-ERRORS-UI:
  Given any component in [feature] that loads async data
  When the request fails
  Then a user-friendly error message is displayed with a retry option

AC-BP-[FEATURE]-A11Y:
  Given all interactive elements in [feature]
  When navigating with keyboard only
  Then all elements are reachable, focusable, and operable with proper ARIA attributes
```

These ACs are automatically added to features with forms:

```
AC-SEC-[FEATURE]-FORM:
  Given a form in [feature]
  When submitting with invalid data
  Then client-side validation shows clear error messages per field and the form is not submitted

AC-BP-[FEATURE]-FORM-UX:
  Given a form in [feature]
  When the user is filling it
  Then the submit button shows loading state during submission and prevents double-submit
```

# Stack Profile: Dart + Flutter

## Coding Best Practices

### Project structure
- Feature-first architecture (`lib/features/[name]/`)
- Each feature: `models/`, `services/`, `screens/`, `widgets/`, `providers/`
- Shared widgets in `lib/common/widgets/`
- Core utilities in `lib/core/` (theme, routing, constants, extensions)
- Use `barrel files` (index.dart) for clean imports

### Conventions
- Follow **Effective Dart** style guide
- Use `const` constructors wherever possible
- Prefer `final` for all local variables
- Name files in `snake_case`, classes in `PascalCase`
- Use `typedef` for complex function types
- Private members prefixed with `_`
- Extensions for utility methods on existing types

### State management
- Use **Riverpod** (recommended) or **BLoC** — choose one and stick with it
- Never use `setState` for complex state — only for simple local UI state
- Separate UI state from business logic
- Use `AsyncValue` (Riverpod) or streams for async state

### Widget rules
- Keep `build()` methods small — extract sub-widgets
- Prefer composition over inheritance for widgets
- Use `const` widgets to optimize rebuilds
- Avoid deep nesting — max 3-4 levels in a single build method
- Use `Builder` pattern for conditional rendering

### Anti-patterns
- Never use `dynamic` — always type explicitly
- Never use `print()` — use `debugPrint()` or a logger
- Never use `late` without guaranteed initialization
- Never ignore lint rules with `// ignore:` without justification
- No business logic in widgets — put it in services/providers
- No hard-coded colors/sizes — use the theme/design system

## Security Rules

### Data storage (OWASP M2, M9)
- Sensitive data (tokens, credentials): use `flutter_secure_storage`
- Never store sensitive data in `SharedPreferences` (not encrypted)
- Clear all secure storage on logout
- Use encrypted database (SQLCipher via Drift) for sensitive local data

### Network security (OWASP M3)
- Use HTTPS only — certificate pinning for production
- Validate all API responses with typed models (freezed/json_serializable)
- Implement request/response interceptors for auth token management
- Handle network errors gracefully — never expose raw error details

### Authentication (OWASP M6)
- Store tokens in secure storage — never in plain text
- Implement biometric auth for sensitive operations
- Auto-lock after inactivity timeout
- Validate JWT token expiry client-side before API calls

### Code protection (OWASP M7, M8)
- Enable code obfuscation for release builds (`--obfuscate --split-debug-info`)
- No debug logging in release builds
- No hardcoded API keys — use `--dart-define` or `.env` files
- Detect rooted/jailbroken devices for sensitive apps

### Platform-specific
- iOS: configure `NSAppTransportSecurity` properly
- Android: set `minSdkVersion` >= 23 for security APIs
- Both: request only needed permissions, explain why (permission rationale)

## Performance Rules
- Use `const` constructors to reduce rebuilds
- Use `ListView.builder` (not `ListView`) for long lists
- Use `CachedNetworkImage` for network images
- Avoid `Opacity` widget — use `FadeTransition` or color opacity
- Profile with Flutter DevTools — watch for jank and excessive rebuilds
- Keep `build()` methods pure — no side effects

## Testing Rules
- Framework: **flutter_test** + **mocktail** (or mockito)
- Widget tests for all screens and complex widgets
- Unit tests for all services and business logic
- Integration tests for critical user journeys
- Use `WidgetTester` for widget interaction tests
- Golden tests for design system components
- Coverage target: 80%+ on business logic

## Auto-generated AC Templates

These ACs are automatically added to EVERY feature with screens:

```
AC-SEC-[FEATURE]-STORAGE:
  Given any data stored locally by [feature]
  When the data contains sensitive information (tokens, PII)
  Then it is stored using flutter_secure_storage, not SharedPreferences

AC-SEC-[FEATURE]-NETWORK:
  Given API calls in [feature]
  When the request fails or times out
  Then a user-friendly error is shown and no sensitive error details are exposed

AC-BP-[FEATURE]-STATE:
  Given the state management for [feature]
  When data changes
  Then only affected widgets rebuild (verified via Flutter DevTools)

AC-BP-[FEATURE]-RESPONSIVE:
  Given any screen in [feature]
  When viewed on different screen sizes (phone, tablet)
  Then the layout adapts properly using responsive breakpoints

AC-BP-[FEATURE]-A11Y-MOBILE:
  Given all interactive elements in [feature]
  When using a screen reader (TalkBack/VoiceOver)
  Then all elements have semantic labels and the flow is logical
```

These ACs are automatically added to features with forms:

```
AC-BP-[FEATURE]-FORM-MOBILE:
  Given a form in [feature]
  When the keyboard opens
  Then the form scrolls properly and input fields are not hidden behind the keyboard

AC-SEC-[FEATURE]-INPUT-MOBILE:
  Given input fields in [feature]
  When entering data
  Then appropriate keyboard types are used and input length is constrained
```

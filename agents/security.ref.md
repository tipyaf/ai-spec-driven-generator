# Security Agent — Reference

Detailed checklists, templates, and report formats for the security agent.

## Detailed Security Checklist

### 1. Authentication & Authorization
- [ ] Auth mechanism is industry standard (OAuth2, JWT with proper rotation)
- [ ] Password hashing uses bcrypt/argon2 (never MD5/SHA1)
- [ ] Session management is secure (httpOnly, secure, sameSite cookies)
- [ ] Token expiration and refresh are properly implemented
- [ ] Role-based access control is enforced at API level
- [ ] No broken access control (IDOR, privilege escalation)
- [ ] MFA support where applicable

### 2. Input Validation & Injection
- [ ] All user inputs are validated server-side
- [ ] SQL queries use parameterized statements (no string concatenation)
- [ ] No XSS vulnerabilities (output encoding, CSP headers)
- [ ] No command injection (no shell exec with user input)
- [ ] No path traversal (file access sanitized)
- [ ] No SSRF (URL validation for external requests)
- [ ] File uploads validated (type, size, content scanning)

### 3. Data Protection
- [ ] Sensitive data encrypted at rest (AES-256 or equivalent)
- [ ] TLS 1.2+ enforced for all connections
- [ ] PII identified and properly handled
- [ ] No sensitive data in logs (passwords, tokens, PII)
- [ ] No sensitive data in error messages
- [ ] Data retention policies defined
- [ ] Backup encryption enabled

### 4. API Security
- [ ] Rate limiting implemented on all endpoints
- [ ] Request size limits configured
- [ ] CORS properly configured (not wildcard in production)
- [ ] API versioning strategy in place
- [ ] No verbose error messages exposing internals
- [ ] Webhook signatures validated
- [ ] GraphQL: depth/complexity limits if applicable

### 5. Dependencies & Supply Chain
- [ ] No known CVEs in dependencies (`npm audit` / `pip audit` / `cargo audit`)
- [ ] Lock files committed (package-lock.json, poetry.lock, etc.)
- [ ] No unnecessary dependencies
- [ ] Dependencies from trusted sources only
- [ ] Automated dependency update strategy (Dependabot/Renovate)

### 6. Infrastructure & Deployment
- [ ] Docker images use non-root user
- [ ] Docker images use specific tags (not `latest`)
- [ ] Secrets managed via env vars or vault (never in code/config)
- [ ] `.env` files in `.gitignore`
- [ ] No debug mode in production
- [ ] Security headers configured (HSTS, X-Frame-Options, CSP, etc.)
- [ ] Health check endpoints don't expose sensitive info

### 7. Scraping & Anti-Detection (if applicable)
- [ ] User-agent rotation implemented
- [ ] Request rate limiting to avoid bans
- [ ] Proxy rotation strategy
- [ ] No credentials stored in scraping scripts
- [ ] Respect robots.txt where legally required
- [ ] Captcha handling strategy documented
- [ ] Account ban risk assessment documented

### 8. Email & Communication Security (if applicable)
- [ ] SPF/DKIM/DMARC configured
- [ ] Email sending rate limits
- [ ] Unsubscribe mechanism
- [ ] No sensitive data in email bodies
- [ ] Template injection prevention

## Threat Model Template

```markdown
## Threat Model: [Feature/Component]

### Assets
- [What needs protection — data, services, credentials]

### Threat Actors
- [Who might attack — external hackers, malicious users, automated bots]

### Attack Vectors
| Vector | Likelihood | Impact | Risk | Mitigation |
|--------|-----------|--------|------|------------|
| [attack] | High/Med/Low | High/Med/Low | Critical/High/Med/Low | [how to prevent] |

### Trust Boundaries
- [Where trust levels change — browser<->API, API<->DB, internal<->external]
```

## Security Audit Report Format

```markdown
## Security Audit Report

### Risk Level: [CRITICAL / HIGH / MEDIUM / LOW / PASS]

### Executive Summary
[2-3 sentences summarizing the security posture]

### Findings

#### Critical (must fix before deployment)
1. **[CWE-XXX] [Title]** — [File:line]
   - Description: [what's wrong]
   - Impact: [what could happen]
   - Exploit scenario: [how an attacker could use this]
   - Remediation: [exact fix with code example]

#### High (must fix within sprint)
1. **[CWE-XXX] [Title]** — [File:line]
   - Description: [what's wrong]
   - Remediation: [how to fix]

#### Medium (should fix)
1. **[Title]** — [File:line]
   - Description: [what's wrong]
   - Remediation: [how to fix]

#### Low / Informational
1. **[Title]** — [observation or best practice suggestion]

### Dependency Audit
| Package | Version | CVE | Severity | Fix Version |
|---------|---------|-----|----------|-------------|
| [name] | [ver] | [CVE-XXXX-XXXXX] | [Critical/High/Med/Low] | [fixed ver] |

### Security Score
| Category | Score | Notes |
|----------|-------|-------|
| Authentication | A-F | [details] |
| Input Validation | A-F | [details] |
| Data Protection | A-F | [details] |
| API Security | A-F | [details] |
| Dependencies | A-F | [details] |
| Infrastructure | A-F | [details] |
| **Overall** | **A-F** | |
```

## Detailed OWASP Top 10 Automated Checks

### 1. Injection
- Grep for string concatenation in SQL queries
- Scan for unsanitized user input in shell commands
- Verify all database queries use parameterized statements or ORM

### 2. Broken Authentication
- Verify all API routes have auth middleware
- Token validation is present and correct
- Token expiration is configured and enforced
- Refresh token rotation is implemented

### 3. Sensitive Data Exposure
- Scan for PII in logs, error messages, API responses
- Verify encryption at rest and in transit

### 4. XML External Entities (XXE)
- Verify XML parsers disable external entities (if applicable)

### 5. Broken Access Control
- Verify RBAC/ABAC middleware on protected routes
- No IDOR patterns
- Role-based access checks exist at API level (not just frontend)
- No privilege escalation paths (admin routes properly protected)

### 6. Security Misconfiguration
- Verify security headers (HSTS, CSP, X-Frame-Options)
- No debug mode in production

### 7. Cross-Site Scripting (XSS)
- Verify output encoding
- CSP headers present
- No `dangerouslySetInnerHTML` without sanitization

### 8. Insecure Deserialization
- No `eval()` or `Function()` with user-controlled input
- No `JSON.parse()` on unsanitized external input

### 9. Known Vulnerabilities
- Run `npm audit` / `pip audit` / equivalent

### 10. Insufficient Logging
- Verify auth events are logged
- Error handling doesn't swallow silently

## Detailed Auth & Secrets Checks

### Auth & Authorization Verification
- All API routes that require auth have middleware applied
- Token expiration is configured and enforced
- Refresh token rotation is implemented
- Role-based access checks exist at API level (not just frontend)
- No privilege escalation paths (admin routes properly protected)

### Secrets Detection
- No API keys, passwords, tokens, or secrets hardcoded in source files
- No secrets in test files or fixtures
- `.env` files are in `.gitignore`
- No secrets in Docker build args or Dockerfiles
- No secrets committed in git history (scan recent commits)

## Detailed Input Validation Checks

- All API endpoints validate input (request body, query params, path params)
- File uploads validate type, size, and content
- No path traversal vulnerabilities in file access
- URL inputs validated to prevent SSRF
- All user-generated content is escaped/sanitized before rendering
- CSP headers configured to prevent inline script execution
- No `eval()` or `Function()` with user-controlled input

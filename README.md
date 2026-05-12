# Contract Portal — Intentionally Vulnerable SPA

> **⚠ WARNING: FOR SECURITY TESTING AND EDUCATION ONLY**
> Do NOT deploy on a public network or production environment.
> All vulnerabilities are intentional.

A deliberately vulnerable Single Page Application built with **Vue.js 3** (frontend) + **Python FastAPI** (backend) + **SQLite** for testing Vulnerability Assessment tools.

---

## Tech Stack

| Layer | Technology | Port |
|-------|-----------|------|
| Frontend | Vue.js 3 + Vite + Vue Router | **3000** |
| Backend | Python FastAPI + PyJWT | **8000** |
| Database | SQLite (file-based) | — |
| Container | Docker + docker-compose | — |

---

## Quick Start

```bash
cd contract-portal
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs (FastAPI Swagger): http://localhost:8000/docs

### Test Accounts

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | admin |
| john | password123 | user |
| jane | jane2024 | user |
| bob | bob123 | user |

---

## Vulnerability List

### API Security
1. **Weak JWT Secret** — `secret123`, no expiry (`POST /api/login`)
2. **CORS Wildcard** — `allow_origins=["*"]`, all methods/headers (all endpoints)
3. **Unauthenticated Legacy Endpoint** — `GET /api/v1/users` returns all users+hashes
4. **Debug/Health Endpoints** — `GET /api/debug` leaks JWT secret + env vars; `GET /api/health` shows package versions
5. **Outdated Dependencies with CVEs** — python-jose 3.2.0, cryptography 3.3.2, PyJWT 1.7.1, axios 0.21.1

### Broken Authentication
6. **No Rate Limiting** on `POST /api/login`
7. **No Account Lockout** — unlimited brute force possible
8. **Password Reset Token Never Expires** — short 8-char token returned directly in response body

### Broken Access Control
9. **IDOR (Read)** — `GET /api/contracts/{id}` returns any contract without ownership check
10. **IDOR (Write)** — `PUT /api/contracts/{id}` edits any contract without ownership check
11. **Missing Role Check** — `GET /api/admin/users` accessible by any authenticated user
12. **Mass Assignment** — `PUT /api/users/{id}` accepts `role` field → privilege escalation

### Injection & Frontend
13. **DOM-based XSS** — URL hash + search query written via `innerHTML` in Dashboard
14. **Stored XSS** — comments stored raw, rendered via `v-html` in ContractDetail
15. **SQL Injection** — `GET /api/search?q=` uses f-string interpolation directly into SQL

### Sensitive Data Exposure
16. **Password Hash in Response** — MD5 hash (no salt) returned by login, `/api/me`, admin
17. **Sensitive Data in localStorage** — token, role, api_key, user_id all stored client-side
18. **Source Maps in Production** — `sourcemap: true` in vite.config.js → `.js.map` exposed
19. **Hardcoded API Key** — `HARDCODED_PAYMENT_API_KEY` in Dashboard.vue source
20. **Stack Trace in Error Response** — full Python traceback + raw SQL query returned to client

### Business Logic
21. **Negative Contract Amount** — no server-side or client-side validation
22. **Skip Approval Workflow** — `status` field can be set to `approved` directly
23. **Clickjacking** — no `X-Frame-Options` or CSP `frame-ancestors` header

---

## File Structure

```
contract-portal/
├── backend/
│   ├── main.py              # FastAPI app (all vulnerabilities marked # VULNERABLE)
│   ├── requirements.txt     # Old packages with CVEs
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/index.js
│   │   └── components/
│   │       ├── Login.vue        # #6, #7, #8, #17
│   │       ├── Dashboard.vue    # #13, #17, #19
│   │       ├── ContractList.vue # #21
│   │       ├── ContractDetail.vue # #9, #10, #13, #14, #22
│   │       ├── AdminPanel.vue   # #11, #12, #16, #17
│   │       └── Profile.vue      # #12, #16, #17
│   ├── vite.config.js       # #18, #23
│   ├── package.json         # Old deps (axios 0.21.1)
│   └── Dockerfile
├── docker-compose.yml
├── VULNERABILITIES.md       # Full table + PoC commands
└── README.md
```

---

## Related

- [VULNERABILITIES.md](VULNERABILITIES.md) — full table with CWE IDs, severities, and PoC commands
- `/hrportal/` — companion PHP vulnerable app

"""
Contract Portal - Backend API
==============================
WARNING: THIS APPLICATION IS INTENTIONALLY VULNERABLE
FOR SECURITY TESTING AND EDUCATION PURPOSES ONLY.
DO NOT DEPLOY IN PRODUCTION.
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sqlite3
import jwt          # VULNERABLE: PyJWT 1.7.1 - CVE-2022-29217
import hashlib
import os
import platform
import sys
import random
import string
import traceback
from typing import Optional

# ─────────────────────────────────────────────────────────────
# VULNERABLE #1: Weak hardcoded JWT secret + no expiry ever set
# ─────────────────────────────────────────────────────────────
JWT_SECRET = "secret123"          # VULNERABLE: Trivially guessable secret
JWT_ALGORITHM = "HS256"
# NOTE: exp claim is never added to any token in this app

# VULNERABLE #19: Hardcoded internal API key (also echoed in /api/debug)
INTERNAL_API_KEY = "sk-internal-corp-prod-9f3a2b1c"

app = FastAPI(
    title="Contract Portal API",
    version="1.0.0",
    debug=True,   # VULNERABLE #20: debug=True leaks stack traces
)

# ─────────────────────────────────────────────────────────────
# VULNERABLE #2: CORS allow ALL origins, methods, and headers
# ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # VULNERABLE: Any origin
    allow_credentials=True,
    allow_methods=["*"],        # VULNERABLE: Any method
    allow_headers=["*"],        # VULNERABLE: Any header
)

# ─────────────────────────────────────────────────────────────
# No X-Frame-Options header middleware → VULNERABLE #23: Clickjacking
# ─────────────────────────────────────────────────────────────
# (Header is simply never set — see also frontend vite.config.js)


# ══════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════

DB_PATH = "/app/data/contracts.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            email       TEXT,
            role        TEXT DEFAULT 'user',
            api_key     TEXT,
            reset_token TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS contracts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            description TEXT,
            amount      REAL,
            status      TEXT DEFAULT 'draft',
            owner_id    INTEGER,
            approved_by INTEGER,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS comments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER,
            user_id     INTEGER,
            content     TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # VULNERABLE #16: Passwords stored as plain MD5 (no salt)
    users = [
        ("admin", "admin123",   "admin@company.internal", "admin", "sk-prod-admin-abc123xyz"),
        ("john",  "password123","john@company.internal",  "user",  "sk-user-john-def456"),
        ("jane",  "jane2024",   "jane@company.internal",  "user",  "sk-user-jane-ghi789"),
        ("bob",   "bob123",     "bob@company.internal",   "user",  "sk-user-bob-jkl012"),
    ]
    for (uname, pwd, email, role, apikey) in users:
        c.execute(
            "INSERT OR IGNORE INTO users (username,password,email,role,api_key) VALUES (?,?,?,?,?)",
            (uname, hashlib.md5(pwd.encode()).hexdigest(), email, role, apikey),
        )

    c.executescript("""
        INSERT OR IGNORE INTO contracts (id,title,description,amount,status,owner_id)
        VALUES (1,'Office Supplies Q1','Quarterly supply contract',5000.00,'approved',1);

        INSERT OR IGNORE INTO contracts (id,title,description,amount,status,owner_id)
        VALUES (2,'IT Equipment Lease','Annual IT lease agreement',50000.00,'pending',2);

        INSERT OR IGNORE INTO contracts (id,title,description,amount,status,owner_id)
        VALUES (3,'Cleaning Services','Monthly cleaning contract',2000.00,'draft',3);

        INSERT OR IGNORE INTO contracts (id,title,description,amount,status,owner_id)
        VALUES (4,'Security Audit 2024','Annual security review',8000.00,'pending',4);
    """)

    conn.commit()
    conn.close()


init_db()


# ══════════════════════════════════════════════════════════════
# AUTH HELPERS
# ══════════════════════════════════════════════════════════════

def get_current_user(request: Request) -> dict:
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        # VULNERABLE #1: Decodes with weak secret, no expiry validation
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


# ══════════════════════════════════════════════════════════════
# AUTH ENDPOINTS
# ══════════════════════════════════════════════════════════════

# VULNERABLE #6 & #7: No rate limiting, no lockout → brute-force login
@app.post("/api/login")
async def login(request: Request):
    try:
        body = await request.json()
        username = body.get("username", "")
        password  = body.get("password", "")

        # VULNERABLE #16: Compare against MD5 hash (no salt, rainbow-table trivial)
        pwd_hash = hashlib.md5(password.encode()).hexdigest()

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, pwd_hash),
        ).fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_dict = dict(user)

        # VULNERABLE #1: JWT has no exp claim → never expires
        token = jwt.encode(
            {
                "user_id":  user_dict["id"],
                "username": user_dict["username"],
                "role":     user_dict["role"],
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        if isinstance(token, bytes):
            token = token.decode("utf-8")

        # VULNERABLE #16: Returns full user row including password hash + api_key
        return {"token": token, "user": user_dict}

    except HTTPException:
        raise
    except Exception as e:
        # VULNERABLE #20: Full stack trace returned to client
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "trace": traceback.format_exc()},
        )


# VULNERABLE #8: Password-reset token never expires, short & predictable
@app.post("/api/forgot-password")
async def forgot_password(request: Request):
    body = await request.json()
    email = body.get("email", "")

    # VULNERABLE #8: 8-char alphanumeric token, no expiry stored
    token = "".join(random.choices(string.ascii_letters + string.digits, k=8))

    conn = get_db()
    conn.execute("UPDATE users SET reset_token=? WHERE email=?", (token, email))
    conn.commit()
    conn.close()

    # VULNERABLE #8: Token returned directly in JSON instead of emailing it
    return {"message": "If email exists, reset link was sent", "debug_token": token}


@app.post("/api/reset-password")
async def reset_password(request: Request):
    body = await request.json()
    token        = body.get("token", "")
    new_password = body.get("password", "")

    conn = get_db()
    # VULNERABLE #8: No expiry check whatsoever
    user = conn.execute(
        "SELECT * FROM users WHERE reset_token=?", (token,)
    ).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    conn.execute(
        "UPDATE users SET password=?, reset_token=NULL WHERE id=?",
        (hashlib.md5(new_password.encode()).hexdigest(), dict(user)["id"]),
    )
    conn.commit()
    conn.close()
    return {"message": "Password reset successful"}


# ══════════════════════════════════════════════════════════════
# LEGACY / DEBUG ENDPOINTS
# ══════════════════════════════════════════════════════════════

# VULNERABLE #3: Legacy v1 endpoint — NO authentication at all
@app.get("/api/v1/users")
async def get_users_v1_no_auth():
    conn = get_db()
    # Returns ALL users including password hashes and api_keys
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return [dict(u) for u in users]


# VULNERABLE #4: Debug endpoint dumps env vars + JWT secret
@app.get("/api/debug")
async def debug_info():
    return {
        "python_version": sys.version,
        "platform":       platform.platform(),
        "hostname":       platform.node(),
        "cwd":            os.getcwd(),
        "db_path":        DB_PATH,
        # VULNERABLE: Leaks secret and internal key
        "jwt_secret":     JWT_SECRET,
        "internal_api_key": INTERNAL_API_KEY,
        "environment":    dict(os.environ),   # leaks ALL env vars
    }


# VULNERABLE #4: Health endpoint reveals package versions & server info
@app.get("/api/health")
async def health():
    return {
        "status":   "ok",
        "server":   platform.node(),
        "os":       f"{platform.system()} {platform.release()}",
        "python":   sys.version,
        "packages": {
            "fastapi":          "0.68.0",
            "python-jose":      "3.2.0",   # CVE-2022-29217
            "PyJWT":            "1.7.1",
            "cryptography":     "3.3.2",   # CVE-2023-23931
            "python-multipart": "0.0.5",   # CVE-2024-24762
            "uvicorn":          "0.15.0",
        },
    }


# ══════════════════════════════════════════════════════════════
# CONTRACTS — IDOR + INJECTION + BUSINESS LOGIC
# ══════════════════════════════════════════════════════════════

@app.get("/api/contracts")
async def list_contracts(request: Request):
    current_user = get_current_user(request)
    conn = get_db()
    # No owner filter — any user sees all contracts
    contracts = conn.execute("SELECT * FROM contracts").fetchall()
    conn.close()
    return [dict(c) for c in contracts]


# VULNERABLE #9: IDOR — GET contract by id, no ownership check
@app.get("/api/contracts/{contract_id}")
async def get_contract(contract_id: int, request: Request):
    current_user = get_current_user(request)   # auth required but no authz
    conn = get_db()
    contract = conn.execute(
        "SELECT * FROM contracts WHERE id=?", (contract_id,)
    ).fetchone()
    conn.close()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    # VULNERABLE #9: Returns any contract regardless of who owns it
    return dict(contract)


# VULNERABLE #10: IDOR — PUT contract by id, no ownership check
# VULNERABLE #21: Accepts negative amounts (business logic)
# VULNERABLE #22: status can jump directly to 'approved' (skip workflow)
@app.put("/api/contracts/{contract_id}")
async def update_contract(contract_id: int, request: Request):
    current_user = get_current_user(request)
    body = await request.json()

    conn = get_db()
    contract = conn.execute(
        "SELECT * FROM contracts WHERE id=?", (contract_id,)
    ).fetchone()
    if not contract:
        conn.close()
        raise HTTPException(status_code=404, detail="Contract not found")

    c = dict(contract)
    conn.execute(
        """UPDATE contracts SET title=?, description=?, amount=?, status=?
           WHERE id=?""",
        (
            body.get("title",       c["title"]),
            body.get("description", c["description"]),
            body.get("amount",      c["amount"]),   # VULNERABLE #21: negative OK
            body.get("status",      c["status"]),   # VULNERABLE #22: direct 'approved'
            contract_id,
        ),
    )
    conn.commit()
    conn.close()
    return {"message": "Contract updated"}


@app.post("/api/contracts")
async def create_contract(request: Request):
    current_user = get_current_user(request)
    body = await request.json()
    conn = get_db()
    # VULNERABLE #21: No validation that amount >= 0
    conn.execute(
        "INSERT INTO contracts (title,description,amount,status,owner_id) VALUES (?,?,?,'draft',?)",
        (body.get("title"), body.get("description"), body.get("amount"), current_user["user_id"]),
    )
    conn.commit()
    conn.close()
    return {"message": "Contract created"}


# VULNERABLE #15: SQL Injection — raw f-string query
@app.get("/api/search")
async def search_contracts(q: str, request: Request):
    current_user = get_current_user(request)
    conn = get_db()
    try:
        # VULNERABLE #15: Direct string interpolation into SQL
        query = f"SELECT * FROM contracts WHERE title LIKE '%{q}%' OR description LIKE '%{q}%'"
        results = conn.execute(query).fetchall()
        conn.close()
        return {"query": query, "results": [dict(r) for r in results]}
    except Exception as e:
        conn.close()
        # VULNERABLE #20: Returns raw SQL error + query + full traceback
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "query": query, "trace": traceback.format_exc()},
        )


# ══════════════════════════════════════════════════════════════
# COMMENTS — Stored XSS
# ══════════════════════════════════════════════════════════════

# VULNERABLE #14: Stored XSS — comment content never sanitized
@app.post("/api/comments")
async def add_comment(request: Request):
    current_user = get_current_user(request)
    body = await request.json()
    conn = get_db()
    # VULNERABLE #14: Raw HTML stored directly, rendered via v-html on frontend
    conn.execute(
        "INSERT INTO comments (contract_id,user_id,content) VALUES (?,?,?)",
        (body.get("contract_id"), current_user["user_id"], body.get("content")),
    )
    conn.commit()
    conn.close()
    return {"message": "Comment added"}


@app.get("/api/comments/{contract_id}")
async def get_comments(contract_id: int, request: Request):
    current_user = get_current_user(request)
    conn = get_db()
    comments = conn.execute(
        "SELECT * FROM comments WHERE contract_id=?", (contract_id,)
    ).fetchall()
    conn.close()
    return [dict(c) for c in comments]


# ══════════════════════════════════════════════════════════════
# USERS
# ══════════════════════════════════════════════════════════════

# VULNERABLE #11: Admin endpoint — no role check, any authenticated user can call it
@app.get("/api/admin/users")
async def admin_list_users(request: Request):
    current_user = get_current_user(request)
    # VULNERABLE #11: No `if current_user["role"] != "admin": raise 403`
    conn = get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    # VULNERABLE #16: Returns password hashes + api_keys for all users
    return [dict(u) for u in users]


# VULNERABLE #12: Mass assignment — role field accepted, no ownership/authz check (IDOR)
@app.put("/api/users/{user_id}")
async def update_user(user_id: int, request: Request):
    current_user = get_current_user(request)
    body = await request.json()

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    u = dict(user)
    conn.execute(
        "UPDATE users SET email=?, role=?, api_key=? WHERE id=?",
        (
            body.get("email",   u["email"]),
            body.get("role",    u["role"]),    # VULNERABLE #12: role escalation
            body.get("api_key", u["api_key"]),
            user_id,                           # VULNERABLE: no ownership check (IDOR)
        ),
    )
    conn.commit()
    conn.close()
    return {"message": "User updated"}


# VULNERABLE #16: /api/me returns full row including password hash + api_key
@app.get("/api/me")
async def get_me(request: Request):
    current_user = get_current_user(request)
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id=?", (current_user["user_id"],)
    ).fetchone()
    conn.close()
    # VULNERABLE #16: password hash + api_key exposed
    return dict(user)

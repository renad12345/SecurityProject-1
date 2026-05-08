# SecurityProject
## Building a Secure Web Application - Detection and Mitigation of Security Vulnerabilities

---

## Project Overview

This project contains two Flask web applications:

- **vulnerable_app.py** - Intentionally insecure app with 5+ vulnerabilities
- **secure_app.py** - Fully secured version with all vulnerabilities fixed

Both apps have: User Registration, Login, Dashboard, Comments, and Admin Panel.

---

## Requirements

- Python 3.x
- Flask
- bcrypt

---

## Setup & Run

### Step 1 - Install libraries (run once only)
```
pip install flask bcrypt
```

### Step 2 - Run Vulnerable App
```
python vulnerable_app.py
```
Open browser: http://localhost:5000

### Step 3 - Run Secure App (open new terminal)
```
python secure_app.py
```
Open browser: https://localhost:5001

Note:
The browser may show "Not Secure" because a self-signed certificate is used.
However, the connection is still encrypted using HTTPS (TLS), In real-world deployment, a trusted certificate authority (CA) such as Let's Encrypt should be used.

---

## Default Admin Account (both apps)

| Field    | Value    |
|----------|----------|
| Username | admin    |
| Password | admin123 |
| Role     | admin    |

---

## How to Test Each Vulnerability

### 1. SQL Injection
- Vulnerable App (port 5000): Go to Login page
  - Username: `' OR '1'='1' --`
  - Password: `anything`
  - Result: Login succeeds without valid credentials
- Secure App (port 5001): Same input fails

### 2. Weak Password (MD5 vs bcrypt)
- Vulnerable App: Register any user, open `users.db` with DB Browser for SQLite
  - Password shows as MD5 hash - paste it at crackstation.net to crack it
- Secure App: Open `users_secure.db`
  - Password shows bcrypt hash starting with `$2b$` - cannot be reversed

### 3. XSS Attack
- Vulnerable App: Login with any account, in the Comments box type:
```
<script>alert('XSS!')</script>
```
  - Click Post - alert popup appears (script executed)
- Secure App: Same input displays as plain text - no popup

### 4. Access Control (RBAC)
- Vulnerable App: Register a new regular user and login
  - Go to: http://localhost:5000/admin
  - You can see the admin panel without being admin
- Secure App: Login as regular user
  - Go to: http://localhost:5001/admin
  - You get 403 Forbidden error
  - Login as admin/admin123 to access admin panel

### 5. Session & Encryption
- Vulnerable App: Secret key is "123" - trivially guessable, no cookie protection flags
- Secure App: Strong random secret key, HttpOnly=True blocks JavaScript from reading cookies,
  SameSite=Lax prevents CSRF attacks
  SESSION_COOKIE_SECURE ensures cookies are only sent over HTTPS
  HTTPS is implemented using Flask ssl_context='adhoc' (self-signed certificate)

---

## Project Files

```
SecurityProject/
├── vulnerable_app.py    (insecure version)
├── secure_app.py        (secure version)
├── README.md            (this file)
├── users.db             (auto-created when vulnerable app runs)
└── users_secure.db      (auto-created when secure app runs)
```

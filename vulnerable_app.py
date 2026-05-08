from flask import Flask, request, redirect, session
import sqlite3
import hashlib

# =========================
# Flask App
# =========================
VulnerableApp = Flask(__name__)

# Weak secret key (intentionally insecure)
VulnerableApp.secret_key = "123"

# =========================
# Database
# =========================
def get_db():
    return sqlite3.connect("users.db")

# =========================
# Setup tables
# =========================
with get_db() as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            role TEXT DEFAULT 'user'
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS comments(
            id INTEGER PRIMARY KEY,
            username TEXT,
            content TEXT
        )
    """)

    existing = db.execute("SELECT * FROM users WHERE username='admin'").fetchone()

    if not existing:
        hashed = hashlib.md5("admin123".encode()).hexdigest()
        db.execute(
            "INSERT INTO users(username, password, role) VALUES('admin', ?, 'admin')",
            (hashed,)
        )

    db.commit()

# =========================
# Home Page (PURPLE UI)
# =========================
@VulnerableApp.route("/")
def home():
    return '''
    <html>
    <head>
    <title>Vulnerable System</title>
    <style>
    *{ margin:0; padding:0; box-sizing:border-box; font-family:Arial,sans-serif; }
    body{ background:linear-gradient(135deg,#1a0b2e,#2d1b4e); min-height:100vh; display:flex; justify-content:center; align-items:center; color:white; }
    .container{ width:900px; display:flex; background:#111827; border-radius:20px; overflow:hidden; box-shadow:0 0 40px rgba(0,0,0,0.6); }
    .left{ flex:1; background:linear-gradient(135deg,#7c3aed,#a855f7); padding:60px 40px; display:flex; flex-direction:column; justify-content:center; }
    .left h1{ font-size:42px; margin-bottom:20px; }
    .left p{ font-size:18px; line-height:1.6; opacity:0.9; }
    .tag{ margin-top:25px; display:inline-block; background:rgba(255,255,255,0.2); padding:10px 18px; border-radius:20px; width:fit-content; font-size:14px; }
    .right{ flex:1; padding:50px; }
    h2{ color:#c4b5fd; margin-bottom:20px; }
    form{ margin-bottom:35px; }
    input{ width:100%; padding:14px; margin-bottom:15px; border:none; border-radius:10px; background:#1e293b; color:white; font-size:15px; }
    button{ width:100%; padding:14px; border:none; border-radius:10px; background:#a855f7; color:white; font-size:16px; font-weight:bold; cursor:pointer; transition:0.3s; }
    button:hover{ background:#9333ea; transform:translateY(-2px); }
    </style>
    </head>
    <body>
    <div class="container">
        <div class="left">
            <h1>Vulnerable System</h1>
            <p> Secure authentication system with protected user access </p>
            <div class="tag"> Vulnerable Version </div>
        </div>
        <div class="right">
            <h2>Register</h2>
            <form action="/register" method="POST">
                <input name="username" placeholder="Username">
                <input name="password" type="password" placeholder="Password">
                <button>Register</button>
            </form>

            <h2>Login</h2>
            <form action="/login" method="POST">
                <input name="username" placeholder="Username">
                <input name="password" type="password" placeholder="Password">
                <button>Login</button>
            </form>
        </div>
    </div>
    </body>
    </html>
    '''

# =========================
# Message Page Function
# =========================
def message_page(message, color="green"):
    return f"""
    <html>
    <head>
    <style>
    body {{
        background: linear-gradient(135deg,#0f172a,#1e293b);
        display:flex;
        justify-content:center;
        align-items:center;
        height:100vh;
        font-family:Arial;
        color:white;
    }}
    .card {{
        background:#1e293b;
        padding:40px;
        border-radius:20px;
        text-align:center;
        box-shadow:0 0 30px rgba(0,0,0,0.5);
        width:350px;
    }}
    .success {{ color:#22c55e; font-size:22px; margin-bottom:20px; }}
    .error {{ color:#ef4444; font-size:22px; margin-bottom:20px; }}
    a {{
        display:inline-block;
        margin-top:20px;
        padding:10px 20px;
        background:#0ea5e9;
        border-radius:10px;
        text-decoration:none;
        color:white;
    }}
    a:hover {{ background:#0284c7; }}
    </style>
    </head>
    <body>
        <div class="card">
            <div class="{color}"> {message} </div>
            <a href="/">Back</a>
        </div>
    </body>
    </html>
    """

# =========================
# Register (VULNERABLE SQL + MD5)
# =========================
@VulnerableApp.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]

    hashed = hashlib.md5(password.encode()).hexdigest()
    db = get_db()

    try:
        db.execute(
            "INSERT INTO users(username, password, role) VALUES(?, ?, 'user')",
            (username, hashed)
        )
        db.commit()
        return message_page("Account created successfully!", "success")

    except sqlite3.IntegrityError:
        return message_page("Username already exists", "error")

# =========================
# Login (SQL Injection + weak hash)
# =========================
@VulnerableApp.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    hashed = hashlib.md5(password.encode()).hexdigest()
    db = get_db()

    user = db.execute(
        f"SELECT * FROM users WHERE username='{username}' AND password='{hashed}'"
    ).fetchone()

    if not user:
        return message_page("Invalid username or password", "error")

    if user:
        session["user"] = username
        session["role"] = user[3]
        return redirect("/dashboard")

# =========================
# Dashboard (XSS vulnerable)
# =========================
@VulnerableApp.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    db = get_db()

    comments = db.execute(
        "SELECT username, content FROM comments"
    ).fetchall()

    comment_html = "".join([
        f"<div style='margin-bottom:10px;background:#1f2937;padding:10px;border-radius:10px'><b>{c[0]}</b>: {c[1]}</div>"
        for c in comments
    ])

    return f"""
    <html>
    <head>
    <title>Dashboard</title>
    <style>
    body{{ background:#1a0b2e; color:white; font-family:Arial; padding:40px; }}
    .topbar{{ display:flex; justify-content:space-between; margin-bottom:30px; }}
    a{{ color:white; text-decoration:none; margin-left:10px; background:#a855f7; padding:10px 15px; border-radius:10px; }}
    .card{{ background:#111827; padding:20px; border-radius:15px; margin-bottom:20px; }}
    input{{ width:100%; padding:12px; margin-top:10px; border-radius:10px; border:none; background:#1e293b; color:white; }}
    button{{ margin-top:10px; padding:10px 15px; background:#a855f7; border:none; border-radius:10px; color:white; }}
    </style>
    </head>
    <body>
        <div class="topbar">
            <h2>Welcome {session['user']}</h2>
            <div>
                <a href="/admin">Admin</a>
                <a href="/logout">Logout</a>
            </div>
        </div>

        <div class="card">
            <h3>Add Comment</h3>
            <form action="/comment" method="POST">
                <input name="content" placeholder="Write something...">
                <button>Post</button>
            </form>
        </div>

        <div class="card">
            <h3>Comments</h3>
            {comment_html}
        </div>
    </body>
    </html>
    """

# =========================
# Comment (XSS vulnerable)
# =========================
@VulnerableApp.route("/comment", methods=["POST"])
def comment():
    if "user" not in session:
        return redirect("/")

    content = request.form["content"]
    db = get_db()

    db.execute(
        "INSERT INTO comments(username, content) VALUES(?, ?)",
        (session["user"], content)
    )

    db.commit()
    return redirect("/dashboard")

# =========================
# Admin (NO RBAC)
# =========================
@VulnerableApp.route("/admin")
def admin():
    if "user" not in session:
        return redirect("/")

    db = get_db()

    users = db.execute(
        "SELECT id, username, role FROM users"
    ).fetchall()

    user_list = "".join([
        f"<li>{u[0]} - {u[1]} - {u[2]}</li>"
        for u in users
    ])

    return f"""
    <html>
    <head>
    <title>Admin Panel (UNSECURED)</title>
    <style>
    body {{ background:#020617; color:white; font-family:Arial; padding:40px; }}
    .container {{ max-width:900px; margin:auto; }}
    .user-card {{ background:#1e293b; padding:20px; border-radius:15px; margin-bottom:15px; }}
    a {{ text-decoration:none; color:white; background:#ef4444; padding:10px 18px; border-radius:10px; display:inline-block; margin-top:20px; }}
    h1 {{ margin-bottom:10px; }}
    .warning {{ color:#f87171; margin-bottom:20px; }}
    </style>
    </head>
    <body>
        <div class="container">
            <h1>Admin Panel (UNSECURED)</h1>
            <p class="warning">This page is accessible to all logged-in users (Vulnerability)</p>
            {user_list}
            <a href='/dashboard'>Back</a>
        </div>
    </body>
    </html>
    """

# =========================
# Logout
# =========================
@VulnerableApp.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =========================
# Run
# =========================
if __name__ == "__main__":
    VulnerableApp.run(debug=True)

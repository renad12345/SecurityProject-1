from flask import Flask, request, redirect, session
import sqlite3
import bcrypt
import html
from functools import wraps

# =========================
# Flask App
# =========================
SecureApp = Flask(__name__)

# Secure secret key
SecureApp.secret_key = "super_secret_key_2024"

# Secure session settings
SecureApp.config["SESSION_COOKIE_HTTPONLY"] = True
SecureApp.config["SESSION_COOKIE_SAMESITE"] = "Lax"
SecureApp.config["SESSION_COOKIE_SECURE"] = True

# =========================
# Database Connection
# =========================
def get_db():
    return sqlite3.connect("users_secure.db")

# =========================
# Create Tables
# =========================
with get_db() as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
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
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        db.execute(
            "INSERT INTO users(username, password, role) VALUES('admin', ?, 'admin')",
            (hashed,)
        )

    db.commit()

# =========================
# Admin Access Decorator
# =========================
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect("/")

        if session.get("role") != "admin":
            return """
            <h1>403 Forbidden</h1>
            <p>Admins only.</p>
            <a href='/dashboard'>Back</a>
            """

        return f(*args, **kwargs)
    return decorated

# =========================
# Home Page
# =========================
@SecureApp.route("/")
def home():
    return '''
    <html>
    <head>
    <title>Secure Web Application</title>
    <style>
    *{ margin:0; padding:0; box-sizing:border-box; font-family:Arial,sans-serif; }
    body{ background:linear-gradient(135deg,#0f172a,#1e293b); min-height:100vh; display:flex; justify-content:center; align-items:center; color:white; }
    .container{ width:900px; display:flex; background:#111827; border-radius:20px; overflow:hidden; box-shadow:0 0 40px rgba(0,0,0,0.5); }
    .left{ flex:1; background:linear-gradient(135deg,#2563eb,#06b6d4); padding:60px 40px; display:flex; flex-direction:column; justify-content:center; }
    .left h1{ font-size:42px; margin-bottom:20px; }
    .left p{ font-size:18px; line-height:1.6; opacity:0.9; }
    .tag{ margin-top:25px; display:inline-block; background:rgba(255,255,255,0.2); padding:10px 18px; border-radius:20px; width:fit-content; font-size:14px; }
    .right{ flex:1; padding:50px; }
    h2{ color:#38bdf8; margin-bottom:20px; }
    form{ margin-bottom:35px; }
    input{ width:100%; padding:14px; margin-bottom:15px; border:none; border-radius:10px; background:#1e293b; color:white; font-size:15px; }
    input:focus{ outline:none; border:2px solid #38bdf8; }
    button{ width:100%; padding:14px; border:none; border-radius:10px; background:#0ea5e9; color:white; font-size:16px; font-weight:bold; cursor:pointer; transition:0.3s; }
    button:hover{ background:#0284c7; transform:translateY(-2px); }
    </style>
    </head>
    <body>
    <div class="container">
        <div class="left">
            <h1>Secure Web App</h1>
            <p> Secure authentication system with protected user access </p>
            <div class="tag">Web Security Project </div>
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
        width:350px;
    }}
    .success {{ color:#22c55e; font-size:22px; }}
    .error {{ color:#ef4444; font-size:22px; }}
    a {{
        display:inline-block;
        margin-top:20px;
        padding:10px 20px;
        background:#0ea5e9;
        border-radius:10px;
        text-decoration:none;
        color:white;
    }}
    </style>
    </head>
    <body>
        <div class="card">
            <div class="{color}">{message}</div>
            <a href="/">Back</a>
        </div>
    </body>
    </html>
    """

# =========================
# Register
# =========================
@SecureApp.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]

    if not username or not password:
        return message_page("Please fill all fields", "error")

    db = get_db()

    existing = db.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    ).fetchone()

    if existing:
        return message_page("Username already exists", "error")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    db.execute(
        "INSERT INTO users(username, password, role) VALUES(?, ?, 'user')",
        (username, hashed)
    )

    db.commit()

    return message_page("Account created successfully!", "success")

# =========================
# Login
# =========================
@SecureApp.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    db = get_db()

    user = db.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    ).fetchone()

    if not user or not bcrypt.checkpw(password.encode(), user[2]):
        return message_page("Invalid username or password", "error")

    session["user"] = username
    session["role"] = user[3]

    return redirect("/dashboard")

# =========================
# Dashboard
# =========================
@SecureApp.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    db = get_db()

    comments = db.execute(
        "SELECT username, content FROM comments"
    ).fetchall()

    comment_html = "".join([
        f"""
        <div class="comment">
            <b>{html.escape(c[0])}</b>
            <p>{html.escape(c[1])}</p>
        </div>
        """ for c in comments
    ])

    return f"""
    <html>
    <head>
    <title>Dashboard</title>
    <style>
    body{{ background:#0f172a; color:white; font-family:Arial; padding:40px; }}
    .topbar{{ display:flex; justify-content:space-between; align-items:center; margin-bottom:40px; }}
    .btn{{ padding:10px 18px; background:#0ea5e9; color:white; border:none; border-radius:10px; text-decoration:none; margin-left:10px; }}
    .card{{ background:#1e293b; padding:25px; border-radius:15px; margin-bottom:30px; }}
    input{{ width:100%; padding:14px; border:none; border-radius:10px; margin-top:10px; margin-bottom:15px; background:#334155; color:white; }}
    button{{ padding:12px 18px; border:none; border-radius:10px; background:#06b6d4; color:white; cursor:pointer; }}
    .comment{{ background:#1e293b; padding:15px; border-radius:10px; margin-top:15px; }}
    </style>
    </head>
    <body>
        <div class="topbar">
            <h1> Welcome {html.escape(session['user'])} </h1>
            <div>
                <a class="btn" href="/admin">Admin</a>
                <a class="btn" href="/logout">Logout</a>
            </div>
        </div>

        <div class="card">
            <h2>XSS Protected Comments</h2>
            <form action="/comment" method="POST">
                <input name="content" placeholder="Write a comment...">
                <button>Post Comment</button>
            </form>
        </div>

        <div class="card">
            <h2>All Comments</h2>
            {comment_html}
        </div>
    </body>
    </html>
    """

# =========================
# Comment
# =========================
@SecureApp.route("/comment", methods=["POST"])
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
# Admin Page
# =========================
@SecureApp.route("/admin")
@admin_required
def admin():
    db = get_db()

    users = db.execute(
        "SELECT id, username, role FROM users"
    ).fetchall()

    user_list = "".join([
        f"""
        <div class="user-card">
            <p><b>ID:</b> {u[0]}</p>
            <p><b>User:</b> {u[1]}</p>
            <p><b>Role:</b> {u[2]}</p>
        </div>
        """ for u in users
    ])

    return f"""
    <html>
    <head>
    <title>Admin Panel</title>
    <style>
    body{{ background:#020617; color:white; font-family:Arial; padding:40px; }}
    .container{{ max-width:900px; margin:auto; }}
    .user-card{{ background:#1e293b; padding:20px; border-radius:15px; margin-bottom:15px; }}
    a{{ text-decoration:none; color:white; background:#0ea5e9; padding:10px 18px; border-radius:10px; display:inline-block; margin-top:20px; }}
    </style>
    </head>
    <body>
        <div class="container">
            <h1>Secure Admin Panel</h1>
            <p> Only admin users can access this page. </p>
            {user_list}
            <a href="/dashboard">Back</a>
        </div>
    </body>
    </html>
    """

# =========================
# Logout
# =========================
@SecureApp.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =========================
# Run App
# =========================
if __name__ == "__main__":
    SecureApp.run(port=5001, debug=True, ssl_context='adhoc')

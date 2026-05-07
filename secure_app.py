from flask import Flask, request, redirect, session
import sqlite3
import bcrypt
import html
from functools import wraps

# Create the Flask application
SecureApp = Flask(__name__)

# Strong secret key for session security
SecureApp.secret_key = "super_secret_key_2024"

# ADDED: Secure session cookie settings
# HttpOnly: blocks JavaScript from reading the cookie
# SameSite: prevents CSRF attacks
SecureApp.config["SESSION_COOKIE_HTTPONLY"] = True
SecureApp.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# In production with HTTPS also enable:
# SecureApp.config["SESSION_COOKIE_SECURE"] = True

# Connect to the database
def get_db():
    return sqlite3.connect("users_secure.db")

# Create users table if it does not exist
with get_db() as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user'
        )
    """)
    # ADDED: comments table for XSS demonstration
    db.execute("""
        CREATE TABLE IF NOT EXISTS comments(
            id INTEGER PRIMARY KEY,
            username TEXT,
            content TEXT
        )
    """)
    # ADDED: default admin account for RBAC testing
    existing = db.execute("SELECT * FROM users WHERE username='admin'").fetchone()
    if not existing:
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        db.execute("INSERT INTO users(username, password, role) VALUES('admin', ?, 'admin')", (hashed,))
    db.commit()

# ADDED: RBAC decorator - restricts access to admin users only
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect("/")
        # Fix: check role before granting access
        if session.get("role") != "admin":
            return "<h1>403 Forbidden</h1><p>Admins only.</p><a href='/dashboard'>Back</a>", 403
        return f(*args, **kwargs)
    return decorated

# Home page - contains register and login forms
@SecureApp.route("/")
def home():
    return '''
    <h2>Register</h2>
    <form action="/register" method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" placeholder="Password"><br><br>
        <button>Register</button>
    </form>
    <h2>Login</h2>
    <form action="/login" method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" placeholder="Password"><br><br>
        <button>Login</button>
    </form>
    '''

# Register route - secured with bcrypt and parameterized queries
@SecureApp.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]

    # bcrypt is a strong hashing algorithm that adds a random salt automatically
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    db = get_db()

    # Parameterized query prevents SQL Injection
    try:
        db.execute("INSERT INTO users(username, password, role) VALUES(?, ?, 'user')", (username, hashed))
        db.commit()
    except sqlite3.IntegrityError:
        return "Username already exists."

    return "Registered! Password stored securely with bcrypt"

# Login route - secured against SQL Injection
@SecureApp.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    db = get_db()

    # Parameterized query - safe from SQL Injection
    user = db.execute(
        "SELECT * FROM users WHERE username=?", (username,)
    ).fetchone()

    # bcrypt.checkpw compares the entered password with the stored hash securely
    if user and bcrypt.checkpw(password.encode(), user[2]):
        session["user"] = username
        session["role"] = user[3]
        return redirect("/dashboard")
    return "Login Failed"

# Dashboard page - only accessible after login
@SecureApp.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    comments = db.execute("SELECT username, content FROM comments").fetchall()

    # ADDED: Fix XSS - html.escape() converts <script> to harmless text
    comment_html = "".join([
        f"<p><b>{html.escape(c[0])}:</b> {html.escape(c[1])}</p>"
        for c in comments
    ])

    return f"""
    <h1>Welcome {html.escape(session['user'])}!</h1>
    <p>Password stored securely with bcrypt</p>
    <p>Protected against SQL Injection</p>
    <a href="/admin">Admin Page</a> | <a href="/logout">Logout</a>
    <h3>Comments (XSS Protected)</h3>
    {comment_html}
    <form action="/comment" method="POST">
        <input name="content" placeholder="Try XSS - it will be escaped">
        <button>Post Comment</button>
    </form>
    """

# ADDED: Comment route - content escaped when displayed
@SecureApp.route("/comment", methods=["POST"])
def comment():
    if "user" not in session:
        return redirect("/")
    content = request.form["content"]
    db = get_db()
    db.execute("INSERT INTO comments(username, content) VALUES(?, ?)", (session["user"], content))
    db.commit()
    return redirect("/dashboard")

# ADDED: Admin page - protected by RBAC decorator
@SecureApp.route("/admin")
@admin_required
def admin():
    db = get_db()
    users = db.execute("SELECT id, username, role FROM users").fetchall()
    user_list = "".join([f"<li>ID:{u[0]} | {u[1]} | Role:{u[2]}</li>" for u in users])
    return f"""
    <h1>Admin Panel (SECURED)</h1>
    <p>Only admin users can access this page.</p>
    <ul>{user_list}</ul>
    <a href="/dashboard">Back</a>
    """

# Logout - clears the session
@SecureApp.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    SecureApp.run(port=5001, debug=True)
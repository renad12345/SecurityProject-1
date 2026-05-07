from flask import Flask, request, redirect, session
import sqlite3
import hashlib

# Create the Flask application
VulnerableApp = Flask(__name__)

# Weak session secret key - intentionally insecure
VulnerableApp.secret_key = "123"

# Connect to the database
def get_db():
    return sqlite3.connect("users.db")

# Create users table if it does not exist
with get_db() as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            username TEXT,
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
        hashed = hashlib.md5("admin123".encode()).hexdigest()
        db.execute("INSERT INTO users(username, password, role) VALUES('admin', ?, 'admin')", (hashed,))
    db.commit()

# Home page - contains register and login forms
@VulnerableApp.route("/")
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

# Register route - vulnerable to SQL Injection and weak password hashing
@VulnerableApp.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]

    # Vulnerability: MD5 is a weak hashing algorithm and easily cracked
    hashed = hashlib.md5(password.encode()).hexdigest()

    db = get_db()

    # Vulnerability: Using f-string makes this vulnerable to SQL Injection
    db.execute(f"INSERT INTO users(username, password, role) VALUES('{username}', '{hashed}', 'user')")
    db.commit()

    return "Registered! Password stored with weak MD5 hash"

# Login route - vulnerable to SQL Injection
@VulnerableApp.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    # Vulnerability: MD5 is weak and can be reversed using online tools
    hashed = hashlib.md5(password.encode()).hexdigest()

    db = get_db()

    # Vulnerability: SQL Injection - attacker can bypass login without a password
    user = db.execute(
        f"SELECT * FROM users WHERE username='{username}' AND password='{hashed}'"
    ).fetchone()

    if user:
        session["user"] = username
        session["role"] = user[3]
        return redirect("/dashboard")
    return "Login Failed"

# Dashboard page - only accessible after login
@VulnerableApp.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    comments = db.execute("SELECT username, content FROM comments").fetchall()

    # Vulnerability: XSS - comments displayed without sanitization
    comment_html = "".join([f"<p><b>{c[0]}:</b> {c[1]}</p>" for c in comments])

    return f"""
    <h1>Welcome {session['user']}!</h1>
    <p>Password stored with weak MD5</p>
    <p>Login vulnerable to SQL Injection</p>
    <a href="/admin">Admin Page</a> | <a href="/logout">Logout</a>
    <h3>Comments (Vulnerable to XSS)</h3>
    {comment_html}
    <form action="/comment" method="POST">
        <input name="content" placeholder="Try: &lt;script&gt;alert('XSS')&lt;/script&gt;">
        <button>Post Comment</button>
    </form>
    """

# ADDED: Comment route - no sanitization, vulnerable to XSS
@VulnerableApp.route("/comment", methods=["POST"])
def comment():
    if "user" not in session:
        return redirect("/")
    content = request.form["content"]
    db = get_db()
    # Vulnerability: content stored and displayed without sanitization
    db.execute("INSERT INTO comments(username, content) VALUES(?, ?)", (session["user"], content))
    db.commit()
    return redirect("/dashboard")

# ADDED: Admin page - no role check, any logged-in user can access
@VulnerableApp.route("/admin")
def admin():
    if "user" not in session:
        return redirect("/")
    # Vulnerability: no role check - any user can see this page
    db = get_db()
    users = db.execute("SELECT id, username, role FROM users").fetchall()
    user_list = "".join([f"<li>ID:{u[0]} | {u[1]} | Role:{u[2]}</li>" for u in users])
    return f"""
    <h1>Admin Panel (UNSECURED)</h1>
    <p>Any logged-in user can access this!</p>
    <ul>{user_list}</ul>
    <a href="/dashboard">Back</a>
    """

# Logout - clears the session
@VulnerableApp.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    VulnerableApp.run(debug=True)
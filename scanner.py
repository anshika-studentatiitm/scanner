from flask import Flask, render_template, request, redirect, session
import sqlite3



app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# Create tables
def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            website TEXT,
            result TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

#login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=? AND password=?",
                            (email, password)).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            return redirect("/dashboard")
        else:
            return "Invalid credentials"

    return render_template("login.html")

#signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        conn.execute("INSERT INTO users (name, phone, email, password) VALUES (?, ?, ?, ?)",
                     (name, phone, email, password))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("signup.html")

#dashboard user
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    result = None

    if request.method == "POST":
        website = request.form["website"]

        # Dummy scan result
        if "https" in website:
            result = "Safe"
        else:
            result = "Vulnerable"

        conn = get_db()
        conn.execute("INSERT INTO history (user_id, website, result) VALUES (?, ?, ?)",
                     (session["user_id"], website, result))
        conn.commit()
        conn.close()

    return render_template("dashboard.html", result=result)

#profile 
@app.route("/profile")
def profile():
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?",
                        (session["user_id"],)).fetchone()
    conn.close()

    return render_template("profile.html", user=user)

#history
@app.route("/history")
def history():
    conn = get_db()
    data = conn.execute("SELECT * FROM history WHERE user_id=?",
                        (session["user_id"],)).fetchall()
    conn.close()

    return render_template("history.html", data=data)

#logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

#main
if __name__ == "__main__":
    app.run(debug=True)


import nmap
import requests

def port_scan(target):
    nm = nmap.PortScanner()
    nm.scan(target, '1-1024')

    results = []

    for host in nm.all_hosts():
        for proto in nm[host].all_protocols():
            ports = nm[host][proto].keys()

            for port in ports:
                state = nm[host][proto][port]['state']
                service = nm[host][proto][port].get('name', 'unknown')

                results.append({
                    "type": "port",
                    "port": port,
                    "state": state,
                    "service": service,
                    "severity": "medium" if port in [21, 23, 3389] else "low"
                })

    return results


def sql_scan(target):
    payload = "' OR '1'='1"
    url = f"http://{target}?id={payload}"

    try:
        r = requests.get(url, timeout=3)

        if "sql" in r.text.lower() or "syntax" in r.text.lower():
            return [{
                "type": "sql",
                "issue": "Possible SQL Injection",
                "severity": "high"
            }]
    except:
        pass

    return []


def xss_scan(target):
    payload = "<script>alert(1)</script>"
    url = f"http://{target}?q={payload}"

    try:
        r = requests.get(url, timeout=3)

        if payload in r.text:
            return [{
                "type": "xss",
                "issue": "Reflected XSS detected",
                "severity": "high"
            }]
    except:
        pass

    return []


def vuln_scan(target):
    results = []

    try:
        r = requests.get(f"http://{target}", timeout=3)
        headers = r.headers

        # Missing security headers
        if "X-Frame-Options" not in headers:
            results.append({
                "type": "vuln",
                "issue": "Missing X-Frame-Options",
                "severity": "medium"
            })

        if "Content-Security-Policy" not in headers:
            results.append({
                "type": "vuln",
                "issue": "Missing CSP",
                "severity": "medium"
            })

    except:
        pass

    return results


def run_scan(target):
    results = []

    results += port_scan(target)
    results += sql_scan(target)
    results += xss_scan(target)
    results += vuln_scan(target)

    return results
from flask import Flask, render_template, request, redirect, session, send_file
from scanner import run_scan
from db import get_db, init_db
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import json

app = Flask(__name__)
app.secret_key = "secret123"

# Initialize DB
init_db()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            return redirect("/dashboard")
        else:
            return "Invalid credentials"

    return render_template("login.html")


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        conn.execute(
            "INSERT INTO users (name, phone, email, password) VALUES (?, ?, ?, ?)",
            (name, phone, email, password)
        )
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("signup.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    results = None

    if request.method == "POST":
        website = request.form["website"]

        # Clean input
        website = website.replace("http://", "").replace("https://", "").strip("/")

        # Run scan
        results = run_scan(website)

        conn = get_db()
        conn.execute(
            "INSERT INTO history (user_id, website, result) VALUES (?, ?, ?)",
            (session["user_id"], website, json.dumps(results))
        )
        conn.commit()
        conn.close()

    return render_template("dashboard.html", results=results)


# ---------------- PROFILE ----------------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()
    conn.close()

    return render_template("profile.html", user=user)


# ---------------- HISTORY ----------------
@app.route("/history")
def history():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM history WHERE user_id=? ORDER BY date DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    data = []
    total_high = 0
    total_medium = 0
    total_low = 0

    for row in rows:
        try:
            results = json.loads(row["result"])
        except json.JSONDecodeError:
            results = []

        for item in results:
            if item.get("severity") == "high":
                total_high += 1
            elif item.get("severity") == "medium":
                total_medium += 1
            else:
                total_low += 1

        data.append({
            "website": row["website"],
            "date": row["date"],
            "results": results
        })

    summary = {
        "high": total_high,
        "medium": total_medium,
        "low": total_low
    }

    return render_template("history.html", data=data, summary=summary)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- REPORT DOWNLOAD ----------------
@app.route("/download-report")
def download_report():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM history WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()

    content = []

    for row in rows:
        content.append(Paragraph(f"Website: {row['website']}", styles["Normal"]))
        content.append(Paragraph(f"Date: {row['date']}", styles["Normal"]))
        content.append(Paragraph("------", styles["Normal"]))

    doc.build(content)

    return send_file("report.pdf", as_attachment=True)


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True)
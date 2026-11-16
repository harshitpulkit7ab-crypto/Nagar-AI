import os
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

from ai_model import calculate_priority, predict_category

BASE_DIR = Path(__file__).resolve().parent
IS_VERCEL = os.environ.get("VERCEL") == "1"
DB_PATH = Path(os.environ.get("NAGARAI_DB_PATH", "/tmp/nagarai.db" if IS_VERCEL else str(BASE_DIR / "nagarai.db")))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            citizen_name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            complaint TEXT NOT NULL,
            category TEXT NOT NULL,
            confidence REAL NOT NULL,
            severity INTEGER NOT NULL,
            public_impact INTEGER NOT NULL,
            affected_people INTEGER NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            location TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_db():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    pending = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status != 'Resolved'"
    ).fetchone()[0]
    resolved = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'"
    ).fetchone()[0]
    critical = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE priority = 'Critical'"
    ).fetchone()[0]

    categories = conn.execute("""
        SELECT category, COUNT(*) AS count
        FROM complaints
        GROUP BY category
        ORDER BY count DESC
        LIMIT 8
    """).fetchall()

    recent = conn.execute("""
        SELECT * FROM complaints
        ORDER BY id DESC
        LIMIT 8
    """).fetchall()
    conn.close()

    return render_template(
        "index.html",
        total=total,
        pending=pending,
        resolved=resolved,
        critical=critical,
        categories=categories,
        recent=recent
    )


@app.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        citizen_name = request.form.get("citizen_name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        complaint = request.form.get("complaint", "").strip()
        location = request.form.get("location", "").strip()

        try:
            severity = int(request.form.get("severity", "3"))
            public_impact = int(request.form.get("public_impact", "3"))
            affected_people = int(request.form.get("affected_people", "3"))
        except ValueError:
            flash("Severity, public impact, and affected people must be numbers from 1 to 5.", "danger")
            return redirect(url_for("submit"))

        if not citizen_name or not complaint:
            flash("Citizen name and complaint are required.", "danger")
            return redirect(url_for("submit"))

        for value, label in [
            (severity, "Severity"),
            (public_impact, "Public impact"),
            (affected_people, "Affected people")
        ]:
            if not 1 <= value <= 5:
                flash(f"{label} must be between 1 and 5.", "danger")
                return redirect(url_for("submit"))

        category, confidence = predict_category(complaint)
        priority, score = calculate_priority(severity, public_impact, affected_people)

        conn = get_db()
        conn.execute("""
            INSERT INTO complaints
            (citizen_name, phone, email, complaint, category, confidence,
             severity, public_impact, affected_people, priority, status,
             location, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
        """, (
            citizen_name,
            phone,
            email,
            complaint,
            category,
            confidence,
            severity,
            public_impact,
            affected_people,
            priority,
            location,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        complaint_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        return render_template(
            "submitted.html",
            complaint_id=complaint_id,
            category=category,
            confidence=confidence,
            priority=priority,
            score=score
        )

    return render_template("submit.html")


@app.route("/complaints")
def complaints():
    status = request.args.get("status", "").strip()
    category = request.args.get("category", "").strip()

    conn = get_db()
    query = "SELECT * FROM complaints WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY id DESC"
    rows = conn.execute(query, params).fetchall()
    cats = conn.execute(
        "SELECT DISTINCT category FROM complaints ORDER BY category"
    ).fetchall()
    conn.close()

    return render_template(
        "complaints.html",
        complaints=rows,
        categories=[c["category"] for c in cats],
        selected_status=status,
        selected_category=category
    )


@app.route("/complaint/<int:complaint_id>/status", methods=["POST"])
def update_status(complaint_id):
    status = request.form.get("status", "Pending")
    allowed = {"Pending", "In Progress", "Resolved"}

    if status not in allowed:
        flash("Invalid status.", "danger")
        return redirect(url_for("complaints"))

    conn = get_db()
    conn.execute(
        "UPDATE complaints SET status = ? WHERE id = ?",
        (status, complaint_id)
    )
    conn.commit()
    conn.close()
    flash("Complaint status updated.", "success")
    return redirect(url_for("complaints"))


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

"""
Brainlab Techies — Flask backend
Single-page marketing site (user side) + authenticated admin dashboard.
SQLite storage for course registrations / free-demo requests.
"""
import os
import json
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash, g, send_file, Response
)
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables from a .env file if present (no hard dependency).
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except Exception:
    # minimal .env parser fallback so a missing python-dotenv doesn't break startup
    _env = os.path.join(BASE_DIR, ".env")
    if os.path.exists(_env):
        with open(_env, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

DB_PATH = os.path.join(BASE_DIR, "brainlab.db")

# --- Groq (AI Career Counsellor) --------------------------------------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("BRAINLAB_SECRET", "brainlab-techies-secret-change-me")

# --- Default admin credentials (override via environment) -------------------
DEFAULT_ADMIN_USER = os.environ.get("BRAINLAB_ADMIN_USER", "admin")
DEFAULT_ADMIN_PASS = os.environ.get("BRAINLAB_ADMIN_PASS", "brainlab@2026")

# Canonical course list used for validation + admin grouping
COURSES = [
    "Data Analytics with Python (Scratch + 1 Project + Certificate)",
    "Data Analytics with Python (Scratch + 3 Projects + Certificate)",
    "Data Analytics with Python (3 Projects + Certificate + Guaranteed Paid Internship + Job Assistance + Interview Grooming)",
    "Python Programming",
    "Power BI",
    "Data Science",
    "Machine Learning",
    "MLOps",
    "Deep Learning",
    "Generative AI",
    "AI Agent Automation (n8n + Zapier)",
]

# Domain themed landing pages. Each background lands on its own themed page.
DOMAINS = {
    "geography": {
        "name": "Geography & Earth Science",
        "accent": "#1f9d63", "accent2": "#2f6bff",
        "tag": "Geoinformatics • Geo-spatial Analytics",
        "headline": "Turn maps, terrain and locations into decisions",
        "intro": "From contour charts and topography to satellite and GIS data — learn to read the Earth with Python and analytics.",
        "fits": ["Geoinformatics", "Geo-spatial Analytics", "Remote Sensing data", "GIS & mapping"],
        "why": [
            ("Spatial data is data", "Your maps, DEMs and survey sheets are datasets waiting to be analysed."),
            ("Python for terrain", "Automate topography, slope and elevation analysis instead of doing it by hand."),
            ("Dashboards of place", "Build Power BI / map dashboards that tell a location story."),
        ],
        "courses": ["Data Analytics with Python (Scratch + 1 Project + Certificate)", "Data Science", "Power BI", "Machine Learning"],
        "theme": "geo",
    },
    "biology": {
        "name": "Biology & Life Sciences",
        "accent": "#0fb6a6", "accent2": "#7a3cff",
        "tag": "Bioinformatics • Biotechnology • Biochemistry",
        "headline": "Decode the data hidden inside life",
        "intro": "Sequences, assays and lab results are data. Learn to analyse them and let machines find the patterns.",
        "fits": ["Bioinformatics", "Biotechnology", "Biochemistry", "Lab & research data"],
        "why": [
            ("From bench to bytes", "Move your lab data into Python and analyse it at scale."),
            ("Patterns in sequences", "Use ML to spot what's hard to see by eye."),
            ("Reproducible research", "Clean, chart and report results like a data scientist."),
        ],
        "courses": ["Data Analytics with Python (Scratch + 3 Projects + Certificate)", "Data Science", "Machine Learning", "Deep Learning"],
        "theme": "bio",
    },
    "it": {
        "name": "IT & Computer Science",
        "accent": "#2f6bff", "accent2": "#8a35ff",
        "tag": "Data & AI Engineering",
        "headline": "Level up from IT into data & AI engineering",
        "intro": "You already speak tech. Add data science, ML systems and production AI to become a high-value engineer.",
        "fits": ["Software / IT students", "CS & BCA / MCA", "Aspiring data engineers", "Backend & web devs"],
        "why": [
            ("Build on what you know", "Your coding base means you move fast into ML and pipelines."),
            ("Ship to production", "Learn MLOps — versioning, deployment and monitoring of models."),
            ("Automate everything", "AI agents with n8n & Zapier to remove repetitive work."),
        ],
        "courses": ["Python Programming", "Machine Learning", "MLOps", "AI Agent Automation (n8n + Zapier)"],
        "theme": "it",
    },
    "aiml": {
        "name": "AI / ML Students",
        "accent": "#8a35ff", "accent2": "#2f6bff",
        "tag": "Deep Learning • MLOps • Generative AI",
        "headline": "Go from coursework to real, deployable AI",
        "intro": "Move past toy notebooks. Build deep-learning models, deploy them, and create with Generative AI.",
        "fits": ["AIML students", "Data science learners", "ML enthusiasts", "Research-minded builders"],
        "why": [
            ("Depth, not just demos", "Neural networks, vision and NLP done properly."),
            ("GenAI in practice", "LLMs, prompting and building real AI products."),
            ("Operate your models", "MLOps so your models survive outside a notebook."),
        ],
        "courses": ["Deep Learning", "MLOps", "Generative AI", "AI Agent Automation (n8n + Zapier)"],
        "theme": "aiml",
    },
    "business": {
        "name": "Finance, Marketing, Sales & Management",
        "accent": "#0e9f6e", "accent2": "#2f6bff",
        "tag": "Finance • Marketing • Sales • Management",
        "headline": "Turn business numbers into an unfair advantage",
        "intro": "Budgets, campaigns, pipelines and KPIs are all data. Learn to analyse them and make sharper, faster decisions.",
        "fits": ["Finance", "Marketing", "Sales", "Management / MBA"],
        "why": [
            ("Decisions, not guesses", "Read revenue, funnels and spend with real analytics instead of gut feel."),
            ("Dashboards that lead", "Build Power BI dashboards leadership actually uses."),
            ("Automate the busywork", "Use AI agents to handle reporting, outreach and follow-ups."),
        ],
        "courses": ["Data Analytics with Python (Scratch + 1 Project + Certificate)", "Power BI", "Data Analytics with Python (3 Projects + Certificate + Guaranteed Paid Internship + Job Assistance + Interview Grooming)", "AI Agent Automation (n8n + Zapier)"],
        "theme": "business",
    },
    "beginners": {
        "name": "Beginners & Career Switchers",
        "accent": "#ff7a59", "accent2": "#8a35ff",
        "tag": "No technical background needed",
        "headline": "No coding idea? Start exactly where you are",
        "intro": "If you've never written a line of code, this is for you. Learn how the modern world runs on data — step by step.",
        "fits": ["Non-technical students", "Career switchers", "Commerce / arts background", "Absolute beginners"],
        "why": [
            ("Truly from scratch", "We assume zero. Every concept is built up patiently."),
            ("Skills, not jargon", "You'll do real, useful things from week one."),
            ("Guided all the way", "Free demo, doubt sessions and a clear path to a job track."),
        ],
        "courses": ["Data Analytics with Python (Scratch + 1 Project + Certificate)", "Python Programming", "Power BI", "Data Analytics with Python (3 Projects + Certificate + Guaranteed Paid Internship + Job Assistance + Interview Grooming)"],
        "theme": "beginners",
    },
}


# --------------------------------------------------------------------------- #
# Database helpers
# --------------------------------------------------------------------------- #
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT,
            academic_background TEXT,
            course TEXT NOT NULL,
            mode TEXT DEFAULT 'Free Demo + Doubt Session',
            message TEXT,
            status TEXT DEFAULT 'New',
            created_at TEXT NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )
    cur = db.execute("SELECT COUNT(*) AS c FROM admins")
    if cur.fetchone()[0] == 0:
        db.execute(
            "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
            (DEFAULT_ADMIN_USER, generate_password_hash(DEFAULT_ADMIN_PASS)),
        )
    db.commit()
    db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


# --------------------------------------------------------------------------- #
# User-facing site
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    return render_template("index.html", courses=COURSES, domains=DOMAINS)


@app.route("/domain/<key>")
def domain(key):
    data = DOMAINS.get(key)
    if not data:
        return redirect(url_for("index"))
    return render_template("domain.html", key=key, d=data, courses=COURSES, domains=DOMAINS)


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    address = (data.get("address") or "").strip()
    academic = (data.get("academic_background") or "").strip()
    course = (data.get("course") or "").strip()
    message = (data.get("message") or "").strip()

    errors = []
    if not name:
        errors.append("Name is required.")
    if not email or "@" not in email:
        errors.append("A valid email is required.")
    if not phone or len(phone) < 7:
        errors.append("A valid phone number is required.")
    if not course:
        errors.append("Please choose a course.")
    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    db = get_db()
    db.execute(
        """INSERT INTO registrations
           (name, email, phone, address, academic_background, course, mode, message, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            name, email, phone, address, academic, course,
            "Free Demo + Doubt Session", message,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    db.commit()
    return jsonify({
        "ok": True,
        "message": "You're registered! Our subject trainer will reach out to schedule your free demo & doubt-clearing session.",
    })


# --------------------------------------------------------------------------- #
# AI Career Counsellor (Groq)
# --------------------------------------------------------------------------- #
COUNSELLOR_SYSTEM = (
    "You are the AI Career Counsellor for Brainlab Techies, a government-registered "
    "ed-tech that trains students in data science, analytics and AI. Your job is to help a "
    "student pick the RIGHT course for their background, goals and time.\n\n"
    "Courses offered:\n"
    "1) Data Analytics with Python - Tier 1 (from scratch + 1 project + certificate)\n"
    "2) Data Analytics with Python - Tier 2 (from scratch + 3 projects + certificate)\n"
    "3) Data Analytics with Python - Tier 3 (3 projects + certificate + GUARANTEED paid internship + job assistance + interview grooming) -> best for placement seekers\n"
    "4) Python Programming  5) Power BI  6) Data Science  7) Machine Learning\n"
    "8) MLOps  9) Deep Learning  10) Generative AI  11) AI Agent Automation with n8n & Zapier\n\n"
    "We welcome EVERY background: Geography (geoinformatics, geo-spatial), Biology (bioinformatics, "
    "biotech, biochemistry), IT, AIML, Finance/Marketing/Sales/Management, and complete beginners with "
    "no coding experience.\n\n"
    "Guidelines: Be warm, concise and practical. Ask 1-2 short questions if you need to know their "
    "background or goal, then recommend a specific course (and tier) and say why. If they want a job, "
    "steer them to Tier 3. Registration is FREE and includes a free demo + doubt-clearing session with "
    "a subject trainer. Encourage them to register for a free demo. Contact: +91 74839 10907. "
    "Keep replies under ~120 words. Never invent prices or guarantees beyond the above."
)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    history = data.get("messages") or []
    if not isinstance(history, list):
        history = []
    # keep only role/content, cap length
    msgs = [{"role": "system", "content": COUNSELLOR_SYSTEM}]
    for m in history[-10:]:
        role = m.get("role")
        content = (m.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            msgs.append({"role": role, "content": content[:1500]})
    if len(msgs) == 1:
        return jsonify({"ok": False, "reply": "Please type a message."}), 400

    if not GROQ_API_KEY:
        return jsonify({
            "ok": False,
            "reply": "The AI counsellor isn't configured yet. Add your GROQ_API_KEY to the .env file and "
                     "restart. Meanwhile, you can register for a free demo and a trainer will guide you.",
        }), 200

    payload = json.dumps({
        "model": GROQ_MODEL,
        "messages": msgs,
        "temperature": 0.6,
        "max_tokens": 400,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        reply = body["choices"][0]["message"]["content"].strip()
        return jsonify({"ok": True, "reply": reply})
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:300]
        app.logger.warning("Groq HTTPError %s: %s", e.code, detail)
        return jsonify({"ok": False, "reply": "The AI counsellor is busy right now. Please try again in a moment, "
                        "or register for a free demo and a trainer will help you personally."}), 200
    except Exception as e:
        app.logger.warning("Groq error: %s", e)
        return jsonify({"ok": False, "reply": "I couldn't reach the AI service. Please check your connection and "
                        "try again — or register for a free demo."}), 200


# --------------------------------------------------------------------------- #
# Admin
# --------------------------------------------------------------------------- #
@app.route("/admin", methods=["GET"])
def admin_root():
    if session.get("admin"):
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("admin_login"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        db = get_db()
        row = db.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            session["admin"] = username
            return redirect(url_for("admin_dashboard"))
        flash("Invalid username or password.")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    db = get_db()
    regs = db.execute("SELECT * FROM registrations ORDER BY id DESC").fetchall()

    # group counts per course
    counts = {}
    for r in regs:
        counts[r["course"]] = counts.get(r["course"], 0) + 1
    by_course = sorted(counts.items(), key=lambda x: -x[1])

    today = datetime.now().strftime("%Y-%m-%d")
    today_count = sum(1 for r in regs if (r["created_at"] or "").startswith(today))

    return render_template(
        "admin_dashboard.html",
        registrations=regs,
        total=len(regs),
        today_count=today_count,
        by_course=by_course,
        admin=session.get("admin"),
    )


@app.route("/admin/registration/<int:reg_id>/status", methods=["POST"])
@login_required
def update_status(reg_id):
    status = (request.form.get("status") or "New").strip()
    db = get_db()
    db.execute("UPDATE registrations SET status = ? WHERE id = ?", (status, reg_id))
    db.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/export.csv")
@login_required
def export_csv():
    db = get_db()
    regs = db.execute("SELECT * FROM registrations ORDER BY id DESC").fetchall()
    lines = ["id,name,email,phone,address,academic_background,course,mode,status,created_at"]
    for r in regs:
        def esc(v):
            v = "" if v is None else str(v)
            v = v.replace('"', '""')
            return f'"{v}"'
        lines.append(",".join(esc(r[k]) for k in
                              ["id", "name", "email", "phone", "address",
                               "academic_background", "course", "mode", "status", "created_at"]))
    return Response(
        "\n".join(lines),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=brainlab_registrations.csv"},
    )


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "5000"))
    print("=" * 60)
    print(" Brainlab Techies is running")
    print(f"  User site : http://127.0.0.1:{port}/")
    print(f"  Admin     : http://127.0.0.1:{port}/admin")
    print(f"  Admin login -> user: {DEFAULT_ADMIN_USER}  pass: {DEFAULT_ADMIN_PASS}")
    print("=" * 60)
    app.run(debug=True, host="127.0.0.1", port=port)

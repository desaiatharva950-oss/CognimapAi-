"""
Cognimap AI - Flask Application & REST API Server
Provides student assessment workflows, interactive knowledge mapping,
personalized learning paths, and lecturer analytics dashboards.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_cors import CORS
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import hashlib
import json
import os
from database import get_db, init_db
from analytics_engine import PrerequisiteGraphEngine, get_status_from_score, STRONG_THRESHOLD, WEAK_THRESHOLD

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cognimap-ai-secure-secret-key-2026")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
CORS(app)

FACULTY_CODE = os.environ.get("FACULTY_CODE", "FACULTY2026")

def hash_password(password: str) -> str:
    """Generate modern salted password hash."""
    return generate_password_hash(password)

def verify_password(stored_hash: str, password: str) -> bool:
    """Verify password against modern salted hash or legacy SHA-256."""
    if not stored_hash or not password:
        return False
    try:
        if check_password_hash(stored_hash, password):
            return True
    except Exception:
        pass
    legacy_hash = hashlib.sha256(password.encode()).hexdigest()
    return stored_hash == legacy_hash

# Keep hash_pw for backward compatibility with existing tests and scripts
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def get_current_user():
    if "user_id" not in session:
        return None
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name, email, role FROM Users WHERE user_id = ?", (session["user_id"],))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

@app.context_processor
def inject_user():
    return {"current_user": get_current_user()}

# ----------------- ROLE-BASED ACCESS CONTROL -----------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized"}), 401
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Unauthorized"}), 401
                flash("Please sign in to access this page.", "warning")
                return redirect(url_for("login", next=request.path))
            if user["role"] not in allowed_roles:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Unauthorized"}), 401
                flash(f"Access denied: {user['role'].capitalize()} accounts cannot access this area.", "danger")
                if user["role"] == "lecturer":
                    return redirect(url_for("lecturer_dashboard"))
                return redirect(url_for("student_dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ----------------- AUTHENTICATION -----------------

@app.route("/")
def index():
    user = get_current_user()
    if user:
        if user["role"] == "lecturer":
            return redirect(url_for("lecturer_dashboard"))
        return redirect(url_for("student_dashboard"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    user = get_current_user()
    if user:
        if user["role"] == "lecturer":
            return redirect(url_for("lecturer_dashboard"))
        return redirect(url_for("student_dashboard"))

    next_url = request.args.get("next") or request.form.get("next")

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name, email, password_hash, role FROM Users WHERE LOWER(email) = ?", (email,))
        user_row = cursor.fetchone()

        if user_row and verify_password(user_row["password_hash"], password):
            # Seamlessly upgrade legacy SHA-256 hash to modern salted hash
            if not user_row["password_hash"].startswith(("scrypt:", "pbkdf2:")):
                upgraded_hash = hash_password(password)
                cursor.execute("UPDATE Users SET password_hash = ? WHERE user_id = ?", (upgraded_hash, user_row["user_id"]))
                conn.commit()
            conn.close()

            session["user_id"] = user_row["user_id"]
            session["user_role"] = user_row["role"]
            session["user_name"] = user_row["name"]
            flash(f"Welcome back, {user_row['name']}!", "success")

            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            if user_row["role"] == "lecturer":
                return redirect(url_for("lecturer_dashboard"))
            return redirect(url_for("student_dashboard"))
        else:
            conn.close()
            flash("Invalid email or password.", "danger")

    return render_template("login.html", next=next_url)

@app.route("/register", methods=["GET", "POST"])
def register():
    user = get_current_user()
    if user:
        if user["role"] == "lecturer":
            return redirect(url_for("lecturer_dashboard"))
        return redirect(url_for("student_dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "student").strip().lower()
        faculty_code = request.form.get("faculty_code", "").strip()

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if role not in ("student", "lecturer"):
            flash("Invalid role selected.", "danger")
            return render_template("register.html")

        if role == "lecturer" and faculty_code != FACULTY_CODE:
            flash(f"Invalid Faculty Verification Code. For evaluation use '{FACULTY_CODE}'.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html")

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Users (name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, (name, email, hash_password(password), role))
            conn.commit()
            uid = cursor.lastrowid
            session["user_id"] = uid
            session["user_role"] = role
            session["user_name"] = name
            flash(f"Account registered successfully as {role.capitalize()}!", "success")
            if role == "lecturer":
                return redirect(url_for("lecturer_dashboard"))
            return redirect(url_for("student_dashboard"))
        except sqlite3.IntegrityError:
            flash("An account with that email already exists.", "danger")
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/demo-login/<role>")
def demo_login(role):
    conn = get_db()
    cursor = conn.cursor()
    if role == "lecturer":
        cursor.execute("SELECT user_id, name, role FROM Users WHERE role = 'lecturer' LIMIT 1")
    else:
        # Student A
        cursor.execute("SELECT user_id, name, role FROM Users WHERE email = 'studentA@cognimap.edu' LIMIT 1")

    user = cursor.fetchone()
    conn.close()

    if user:
        session["user_id"] = user["user_id"]
        session["user_role"] = user["role"]
        session["user_name"] = user["name"]
        flash(f"Logged in as demo {role.capitalize()}: {user['name']}", "info")
        if user["role"] == "lecturer":
            return redirect(url_for("lecturer_dashboard"))
        return redirect(url_for("student_dashboard"))

    flash("Demo user not found. Please initialize seed data.", "danger")
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))

# ----------------- STUDENT WORKFLOWS -----------------

@app.route("/dashboard")
@role_required("student")
def student_dashboard():
    user = get_current_user()

    conn = get_db()
    cursor = conn.cursor()

    # Active course details from persistent database
    cursor.execute("SELECT subject_id, subject_name, code, description FROM Subjects LIMIT 1")
    subj_row = cursor.fetchone()
    subject = dict(subj_row) if subj_row else None

    # Get student's latest attempts
    cursor.execute("""
        SELECT a.attempt_id, a.assessment_id, a.score, a.max_score, a.percentage,
               a.completed_at, asm.title, asm.assessment_type
        FROM StudentAttempts a
        JOIN Assessments asm ON a.assessment_id = asm.assessment_id
        WHERE a.student_id = ?
        ORDER BY a.attempt_id DESC
    """, (user["user_id"],))
    attempts = [dict(r) for r in cursor.fetchall()]

    # Available assessments
    cursor.execute("""
        SELECT a.assessment_id, a.title, a.assessment_type, a.duration_minutes, s.subject_name
        FROM Assessments a
        JOIN Subjects s ON a.subject_id = s.subject_id
    """)
    assessments = [dict(r) for r in cursor.fetchall()]

    # Get latest concept performance
    cursor.execute("""
        SELECT c.concept_id, c.concept_name, cp.score, cp.status, t.topic_name, u.unit_name
        FROM ConceptPerformance cp
        JOIN Concepts c ON cp.concept_id = c.concept_id
        JOIN Topics t ON c.topic_id = t.topic_id
        JOIN Units u ON t.unit_id = u.unit_id
        JOIN (
            SELECT concept_id, MAX(performance_id) as max_id
            FROM ConceptPerformance
            WHERE student_id = ?
            GROUP BY concept_id
        ) latest ON cp.performance_id = latest.max_id
        ORDER BY cp.score ASC
    """, (user["user_id"],))
    concepts_perf = [dict(r) for r in cursor.fetchall()]

    # Prerequisite gap detection
    engine = PrerequisiteGraphEngine(conn)
    score_map = {c["concept_id"]: c["score"] for c in concepts_perf}
    prereq_gaps = engine.detect_prerequisite_gaps(score_map)

    # Learning path — deduplicated: one step per concept, latest score
    cursor.execute("""
        SELECT lp.priority, lp.recommendation_reason, lp.is_prerequisite_gap,
               c.concept_name, c.concept_id, cp.score, cp.status
        FROM LearningPaths lp
        JOIN Concepts c ON lp.concept_id = c.concept_id
        LEFT JOIN (
            SELECT cp2.concept_id, cp2.score, cp2.status
            FROM ConceptPerformance cp2
            JOIN (
                SELECT concept_id, MAX(performance_id) as max_id
                FROM ConceptPerformance
                WHERE student_id = ?
                GROUP BY concept_id
            ) latest ON cp2.performance_id = latest.max_id
        ) cp ON c.concept_id = cp.concept_id
        WHERE lp.student_id = ?
        GROUP BY lp.concept_id
        ORDER BY lp.priority ASC
    """, (user["user_id"], user["user_id"]))
    learning_path = [dict(r) for r in cursor.fetchall()]

    # Follow-up improvement record if any
    cursor.execute("""
        SELECT f.previous_overall_score, f.new_overall_score, f.overall_improvement,
               f.concept_improvements_json, f.created_at
        FROM FollowUpAssessments f
        WHERE f.student_id = ?
        ORDER BY f.followup_id DESC LIMIT 1
    """, (user["user_id"],))
    followup_row = cursor.fetchone()
    followup_data = dict(followup_row) if followup_row else None
    if followup_data:
        followup_data["concept_improvements"] = json.loads(followup_data["concept_improvements_json"])

    # Categorize counts
    strong_count = sum(1 for c in concepts_perf if c["status"] == "Strong")
    improve_count = sum(1 for c in concepts_perf if c["status"] == "Needs Improvement")
    weak_count = sum(1 for c in concepts_perf if c["status"] == "Weak")

    conn.close()

    return render_template("student_dashboard.html",
        user=user,
        subject=subject,
        attempts=attempts,
        assessments=assessments,
        concepts_perf=concepts_perf,
        prereq_gaps=prereq_gaps,
        learning_path=learning_path,
        followup_data=followup_data,
        strong_count=strong_count,
        improve_count=improve_count,
        weak_count=weak_count
    )

@app.route("/assessment/<int:assessment_id>")
@role_required("student")
def take_assessment(assessment_id):
    user = get_current_user()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.assessment_id, a.title, a.assessment_type, a.duration_minutes, s.subject_name
        FROM Assessments a
        JOIN Subjects s ON a.subject_id = s.subject_id
        WHERE a.assessment_id = ?
    """, (assessment_id,))
    assessment = cursor.fetchone()
    if not assessment:
        conn.close()
        flash("Assessment not found.", "danger")
        return redirect(url_for("student_dashboard"))

    # Fetch questions
    cursor.execute("""
        SELECT q.question_id, q.question_text, q.difficulty, q.options_json, q.marks,
               c.concept_name, c.concept_id, t.topic_name, u.unit_name
        FROM AssessmentQuestions aq
        JOIN Questions q ON aq.question_id = q.question_id
        JOIN Concepts c ON q.concept_id = c.concept_id
        JOIN Topics t ON c.topic_id = t.topic_id
        JOIN Units u ON t.unit_id = u.unit_id
        WHERE aq.assessment_id = ?
        ORDER BY q.difficulty ASC, q.question_id ASC
    """, (assessment_id,))
    raw_questions = cursor.fetchall()

    questions = []
    for r in raw_questions:
        q_dict = dict(r)
        q_dict["options"] = json.loads(r["options_json"])
        questions.append(q_dict)

    conn.close()

    return render_template("assessment.html",
        assessment=dict(assessment),
        questions=questions
    )

@app.route("/api/submit-assessment", methods=["POST"])
@role_required("student")
def submit_assessment():
    user = get_current_user()

    data = request.get_json() or {}
    assessment_id = data.get("assessment_id")
    answers = data.get("answers", {})  # { question_id: selected_option }
    time_taken = data.get("time_taken_seconds", 0)

    if not assessment_id:
        return jsonify({"error": "Missing assessment ID"}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Create new attempt entry
    cursor.execute("""
        INSERT INTO StudentAttempts (student_id, assessment_id, score, max_score, percentage, time_taken_seconds)
        VALUES (?, ?, 0, 0, 0, ?)
    """, (user["user_id"], assessment_id, time_taken))
    attempt_id = cursor.lastrowid

    # Fetch correct answers and marks for submitted questions
    cursor.execute("""
        SELECT q.question_id, q.correct_answer, q.marks
        FROM AssessmentQuestions aq
        JOIN Questions q ON aq.question_id = q.question_id
        WHERE aq.assessment_id = ?
    """, (assessment_id,))
    q_map = {str(r["question_id"]): dict(r) for r in cursor.fetchall()}

    for qid_str, q_info in q_map.items():
        qid = int(qid_str)
        selected = answers.get(qid_str, "")
        correct = 1 if selected == q_info["correct_answer"] else 0
        marks_awarded = q_info["marks"] if correct else 0

        cursor.execute("""
            INSERT INTO StudentAnswers (attempt_id, question_id, selected_answer, correctness, marks_awarded)
            VALUES (?, ?, ?, ?, ?)
        """, (attempt_id, qid, selected, correct, marks_awarded))

    conn.commit()

    # Run intelligent analysis engine
    engine = PrerequisiteGraphEngine(conn)
    analysis = engine.analyze_attempt(attempt_id)

    # Check if this was a follow-up assessment to compare with initial
    cursor.execute("SELECT assessment_type FROM Assessments WHERE assessment_id = ?", (assessment_id,))
    asm_type_row = cursor.fetchone()
    if asm_type_row and asm_type_row["assessment_type"] == "followup":
        # Find latest initial attempt
        cursor.execute("""
            SELECT a.attempt_id FROM StudentAttempts a
            JOIN Assessments asm ON a.assessment_id = asm.assessment_id
            WHERE a.student_id = ? AND asm.assessment_type = 'initial'
            ORDER BY a.attempt_id DESC LIMIT 1
        """, (user["user_id"],))
        init_att = cursor.fetchone()
        if init_att:
            imp_res = engine.compute_improvement(init_att["attempt_id"], attempt_id)
            cursor.execute("""
                INSERT INTO FollowUpAssessments (student_id, initial_assessment_id, followup_attempt_id, previous_overall_score, new_overall_score, overall_improvement, concept_improvements_json)
                VALUES (?, (SELECT assessment_id FROM StudentAttempts WHERE attempt_id = ?), ?, ?, ?, ?, ?)
            """, (user["user_id"], init_att["attempt_id"], attempt_id, imp_res["initial_overall"], imp_res["followup_overall"], imp_res["overall_delta"], json.dumps(imp_res["concepts"])))
            conn.commit()
            analysis["followup_improvement"] = imp_res

    conn.close()

    is_followup = asm_type_row and asm_type_row["assessment_type"] == "followup"
    redirect_url = url_for("followup_quiz_view") if is_followup else url_for("diagnostic_report", attempt_id=attempt_id)

    return jsonify({
        "success": True,
        "attempt_id": attempt_id,
        "analysis": analysis,
        "redirect_url": redirect_url
    })

@app.route("/diagnostic-report/<int:attempt_id>")
@login_required
def diagnostic_report(attempt_id):
    user = get_current_user()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.attempt_id, a.score, a.max_score, a.percentage, a.completed_at, a.time_taken_seconds,
               asm.title, asm.assessment_type, u.name as student_name, u.user_id as student_id
        FROM StudentAttempts a
        JOIN Assessments asm ON a.assessment_id = asm.assessment_id
        JOIN Users u ON a.student_id = u.user_id
        WHERE a.attempt_id = ?
    """, (attempt_id,))
    attempt = cursor.fetchone()
    if not attempt:
        conn.close()
        flash("Attempt not found.", "danger")
        return redirect(url_for("student_dashboard"))

    # Security check: students can only see their own reports (unless lecturer)
    if user["role"] == "student" and attempt["student_id"] != user["user_id"]:
        conn.close()
        flash("Unauthorized access.", "danger")
        return redirect(url_for("student_dashboard"))

    # Fetch concept breakdown
    cursor.execute("""
        SELECT c.concept_name, cp.score, cp.status, cp.total_questions, cp.correct_questions,
               t.topic_name, u.unit_name
        FROM ConceptPerformance cp
        JOIN Concepts c ON cp.concept_id = c.concept_id
        JOIN Topics t ON c.topic_id = t.topic_id
        JOIN Units u ON t.unit_id = u.unit_id
        WHERE cp.assessment_id = (SELECT assessment_id FROM StudentAttempts WHERE attempt_id = ?)
          AND cp.student_id = ?
        ORDER BY cp.score ASC
    """, (attempt_id, attempt["student_id"]))
    concept_rows = [dict(r) for r in cursor.fetchall()]

    # Fetch questions and review
    cursor.execute("""
        SELECT q.question_text, q.difficulty, q.options_json, q.correct_answer, q.explanation,
               sa.selected_answer, sa.correctness, sa.marks_awarded, c.concept_name
        FROM StudentAnswers sa
        JOIN Questions q ON sa.question_id = q.question_id
        JOIN Concepts c ON q.concept_id = c.concept_id
        WHERE sa.attempt_id = ?
        ORDER BY sa.answer_id ASC
    """, (attempt_id,))
    review_rows = []
    for r in cursor.fetchall():
        rd = dict(r)
        rd["options"] = json.loads(r["options_json"])
        review_rows.append(rd)

    # Prerequisite gaps
    engine = PrerequisiteGraphEngine(conn)
    cursor.execute("SELECT concept_id, score FROM ConceptPerformance WHERE assessment_id = (SELECT assessment_id FROM StudentAttempts WHERE attempt_id = ?) AND student_id = ?", (attempt_id, attempt["student_id"]))
    score_map = {r["concept_id"]: r["score"] for r in cursor.fetchall()}
    prereq_gaps = engine.detect_prerequisite_gaps(score_map)

    conn.close()

    return render_template("diagnostic_report.html",
        attempt=dict(attempt),
        concepts=concept_rows,
        reviews=review_rows,
        prereq_gaps=prereq_gaps
    )

@app.route("/knowledge-map")
@login_required
def knowledge_map_view():
    user = get_current_user()
    return render_template("knowledge_map.html", user=user)

@app.route("/api/knowledge-map")
def api_knowledge_map():
    user = get_current_user()
    if user and user["role"] == "student":
        # Prevent IDOR: students can only see their own knowledge map
        sid = user["user_id"]
    elif user and user["role"] == "lecturer":
        # Lecturer can inspect class aggregate (None) or drill down into specific student
        sid = request.args.get("student_id", type=int)
    else:
        sid = None

    conn = get_db()
    engine = PrerequisiteGraphEngine(conn)
    map_data = engine.get_knowledge_map_data(student_id=sid)
    conn.close()

    return jsonify(map_data)

@app.route("/learning-path")
@role_required("student")
def learning_path_view():
    user = get_current_user()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT lp.priority, lp.recommendation_reason, lp.is_prerequisite_gap,
               c.concept_id, c.concept_name, c.description, c.explanation_md, c.key_points, c.code_example,
               t.topic_name, u.unit_name, cp.score, cp.status
        FROM LearningPaths lp
        JOIN Concepts c ON lp.concept_id = c.concept_id
        JOIN Topics t ON c.topic_id = t.topic_id
        JOIN Units u ON t.unit_id = u.unit_id
        LEFT JOIN (
            SELECT concept_id, score, status FROM ConceptPerformance
            WHERE student_id = ?
        ) cp ON c.concept_id = cp.concept_id
        WHERE lp.student_id = ?
        ORDER BY lp.priority ASC
    """, (user["user_id"], user["user_id"]))
    steps = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return render_template("learning_path.html", steps=steps, user=user)

@app.route("/followup-quiz")
@role_required("student")
def followup_quiz_view():
    user = get_current_user()

    conn = get_db()
    cursor = conn.cursor()

    # Get follow-up assessment ID
    cursor.execute("SELECT assessment_id FROM Assessments WHERE assessment_type = 'followup' ORDER BY assessment_id DESC LIMIT 1")
    f_asm = cursor.fetchone()

    # Get improvement record if already completed
    cursor.execute("""
        SELECT f.previous_overall_score, f.new_overall_score, f.overall_improvement,
               f.concept_improvements_json, f.created_at, f.followup_attempt_id
        FROM FollowUpAssessments f
        WHERE f.student_id = ?
        ORDER BY f.followup_id DESC LIMIT 1
    """, (user["user_id"],))
    followup_row = cursor.fetchone()
    followup_data = dict(followup_row) if followup_row else None
    if followup_data:
        followup_data["concept_improvements"] = json.loads(followup_data["concept_improvements_json"])

    conn.close()

    return render_template("followup_quiz.html",
        user=user,
        followup_id=f_asm["assessment_id"] if f_asm else None,
        followup_data=followup_data
    )

# ----------------- LECTURER WORKFLOWS -----------------

@app.route("/lecturer")
@role_required("lecturer")
def lecturer_dashboard():
    user = get_current_user()

    conn = get_db()
    cursor = conn.cursor()

    # Active course details from persistent database
    cursor.execute("SELECT subject_id, subject_name, code, description FROM Subjects WHERE lecturer_id = ? LIMIT 1", (user["user_id"],))
    subj_row = cursor.fetchone()
    if not subj_row:
        cursor.execute("SELECT subject_id, subject_name, code, description FROM Subjects LIMIT 1")
        subj_row = cursor.fetchone()
    subject = dict(subj_row) if subj_row else None

    # Class stats
    cursor.execute("SELECT COUNT(DISTINCT student_id) as total_students FROM StudentAttempts")
    total_students = cursor.fetchone()["total_students"]

    cursor.execute("""
        SELECT ROUND(AVG(best_pct), 1) as class_avg FROM (
            SELECT student_id, MAX(percentage) as best_pct FROM StudentAttempts GROUP BY student_id
        )
    """)
    class_avg = cursor.fetchone()["class_avg"] or 0.0

    # Score distribution: strong / needs-improvement / weak (best attempt per student)
    cursor.execute("""
        SELECT
            SUM(CASE WHEN best_pct >= 75 THEN 1 ELSE 0 END) as strong_count,
            SUM(CASE WHEN best_pct >= 50 AND best_pct < 75 THEN 1 ELSE 0 END) as ni_count,
            SUM(CASE WHEN best_pct < 50 THEN 1 ELSE 0 END) as weak_count
        FROM (
            SELECT student_id, MAX(percentage) as best_pct FROM StudentAttempts GROUP BY student_id
        )
    """)
    dist = cursor.fetchone()
    score_distribution = {
        "strong": dist["strong_count"] or 0,
        "needs_improvement": dist["ni_count"] or 0,
        "weak": dist["weak_count"] or 0
    }

    cursor.execute("SELECT COUNT(*) as total_assessments FROM Assessments")
    total_assessments = cursor.fetchone()["total_assessments"]

    cursor.execute("SELECT COUNT(*) as total_questions FROM Questions")
    total_questions = cursor.fetchone()["total_questions"]

    # Knowledge gaps — deduplicated (latest per student+concept)
    cursor.execute("""
        SELECT c.concept_id, c.concept_name,
               ROUND(AVG(cp.score), 1) as avg_score,
               COUNT(DISTINCT cp.student_id) as students_tested,
               SUM(CASE WHEN cp.status = 'Weak' THEN 1 ELSE 0 END) as weak_count,
               SUM(CASE WHEN cp.status = 'Needs Improvement' THEN 1 ELSE 0 END) as ni_count,
               SUM(CASE WHEN cp.status = 'Strong' THEN 1 ELSE 0 END) as strong_count,
               ROUND(100.0 * (SUM(CASE WHEN cp.status IN ('Weak','Needs Improvement') THEN 1 ELSE 0 END)) / COUNT(DISTINCT cp.student_id), 1) as need_improvement_pct
        FROM ConceptPerformance cp
        JOIN Concepts c ON cp.concept_id = c.concept_id
        JOIN (
            SELECT concept_id, student_id, MAX(performance_id) as max_id
            FROM ConceptPerformance GROUP BY concept_id, student_id
        ) latest ON cp.performance_id = latest.max_id
        GROUP BY c.concept_id, c.concept_name
        ORDER BY need_improvement_pct DESC
    """)
    knowledge_gaps = [dict(r) for r in cursor.fetchall()]

    # Per-student roster: best score, attempts, concept mastery breakdown
    cursor.execute("""
        SELECT u.user_id, u.name, u.email,
               COALESCE(stats.attempt_count, 0) as attempt_count,
               stats.best_pct as percentage,
               stats.last_attempt_at as completed_at,
               f.overall_improvement,
               COALESCE(cp_counts.strong_concepts, 0) as strong_concepts,
               COALESCE(cp_counts.weak_concepts, 0) as weak_concepts,
               COALESCE(cp_counts.total_concepts, 0) as total_concepts
        FROM Users u
        LEFT JOIN (
            SELECT student_id, COUNT(*) as attempt_count,
                   MAX(percentage) as best_pct, MAX(completed_at) as last_attempt_at
            FROM StudentAttempts GROUP BY student_id
        ) stats ON u.user_id = stats.student_id
        LEFT JOIN (
            SELECT f2.student_id, f2.overall_improvement
            FROM FollowUpAssessments f2
            JOIN (SELECT student_id, MAX(followup_id) as max_fid FROM FollowUpAssessments GROUP BY student_id) lf
            ON f2.followup_id = lf.max_fid
        ) f ON u.user_id = f.student_id
        LEFT JOIN (
            SELECT cp.student_id,
                   SUM(CASE WHEN cp.status='Strong' THEN 1 ELSE 0 END) as strong_concepts,
                   SUM(CASE WHEN cp.status='Weak' THEN 1 ELSE 0 END) as weak_concepts,
                   COUNT(DISTINCT cp.concept_id) as total_concepts
            FROM ConceptPerformance cp
            JOIN (
                SELECT concept_id, student_id, MAX(performance_id) as max_id
                FROM ConceptPerformance GROUP BY concept_id, student_id
            ) latest ON cp.performance_id = latest.max_id
            GROUP BY cp.student_id
        ) cp_counts ON u.user_id = cp_counts.student_id
        WHERE u.role = 'student'
        ORDER BY stats.best_pct DESC, u.name ASC
    """)
    students = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return render_template("lecturer_dashboard.html",
        user=user,
        subject=subject,
        total_students=total_students,
        class_avg=class_avg,
        total_assessments=total_assessments,
        total_questions=total_questions,
        score_distribution=score_distribution,
        knowledge_gaps=knowledge_gaps,
        students=students
    )

@app.route("/lecturer/student/<int:student_id>")
@role_required("lecturer")
def lecturer_student_drilldown(student_id):
    user = get_current_user()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, name, email FROM Users WHERE user_id = ? AND role = 'student'", (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        flash("Student not found.", "danger")
        return redirect(url_for("lecturer_dashboard"))

    cursor.execute("""
        SELECT a.attempt_id, a.score, a.max_score, a.percentage, a.completed_at, asm.title, asm.assessment_type
        FROM StudentAttempts a
        JOIN Assessments asm ON a.assessment_id = asm.assessment_id
        WHERE a.student_id = ?
        ORDER BY a.attempt_id DESC
    """, (student_id,))
    attempts = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT c.concept_id, c.concept_name, cp.score, cp.status, t.topic_name, u.unit_name
        FROM ConceptPerformance cp
        JOIN Concepts c ON cp.concept_id = c.concept_id
        JOIN Topics t ON c.topic_id = t.topic_id
        JOIN Units u ON t.unit_id = u.unit_id
        JOIN (
            SELECT concept_id, MAX(performance_id) as max_id
            FROM ConceptPerformance
            WHERE student_id = ?
            GROUP BY concept_id
        ) latest ON cp.performance_id = latest.max_id
        ORDER BY cp.score ASC
    """, (student_id,))
    concepts = [dict(r) for r in cursor.fetchall()]

    # Learning Path
    cursor.execute("""
        SELECT lp.priority, lp.recommendation_reason, lp.is_prerequisite_gap, c.concept_name
        FROM LearningPaths lp
        JOIN Concepts c ON lp.concept_id = c.concept_id
        WHERE lp.student_id = ?
        ORDER BY lp.priority ASC
    """, (student_id,))
    learning_path = [dict(r) for r in cursor.fetchall()]

    # Follow-up improvement
    cursor.execute("""
        SELECT f.previous_overall_score, f.new_overall_score, f.overall_improvement, f.concept_improvements_json
        FROM FollowUpAssessments f
        WHERE f.student_id = ?
        ORDER BY f.followup_id DESC LIMIT 1
    """, (student_id,))
    followup_row = cursor.fetchone()
    followup_data = dict(followup_row) if followup_row else None
    if followup_data:
        followup_data["concept_improvements"] = json.loads(followup_data["concept_improvements_json"])

    # Prerequisite gap detection
    engine = PrerequisiteGraphEngine(conn)
    score_map = {c["concept_id"]: c["score"] for c in concepts}
    prereq_gaps = engine.detect_prerequisite_gaps(score_map)

    conn.close()

    return render_template("lecturer_student_drilldown.html",
        student=dict(student),
        attempts=attempts,
        concepts=concepts,
        learning_path=learning_path,
        followup_data=followup_data,
        prereq_gaps=prereq_gaps
    )

@app.route("/lecturer/curriculum")
@role_required("lecturer")
def lecturer_curriculum():
    user = get_current_user()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.unit_id, u.unit_number, u.unit_name,
               t.topic_id, t.topic_name,
               c.concept_id, c.concept_name, c.description
        FROM Units u
        LEFT JOIN Topics t ON u.unit_id = t.unit_id
        LEFT JOIN Concepts c ON t.topic_id = c.topic_id
        ORDER BY u.unit_number ASC, t.topic_id ASC, c.concept_id ASC
    """)
    rows = cursor.fetchall()

    curriculum = {}
    for r in rows:
        uid = r["unit_id"]
        if uid not in curriculum:
            curriculum[uid] = {
                "unit_id": uid,
                "unit_number": r["unit_number"],
                "unit_name": r["unit_name"],
                "topics": {}
            }
        tid = r["topic_id"]
        if tid:
            if tid not in curriculum[uid]["topics"]:
                curriculum[uid]["topics"][tid] = {
                    "topic_id": tid,
                    "topic_name": r["topic_name"],
                    "concepts": []
                }
            if r["concept_id"]:
                curriculum[uid]["topics"][tid]["concepts"].append({
                    "concept_id": r["concept_id"],
                    "concept_name": r["concept_name"],
                    "description": r["description"]
                })

    # Prerequisite edges
    cursor.execute("""
        SELECT cd.dependency_id, cd.concept_id as target_id, cd.prerequisite_concept_id as prereq_id,
               c1.concept_name as prerequisite_name, c2.concept_name as target_name
        FROM ConceptDependencies cd
        JOIN Concepts c1 ON cd.prerequisite_concept_id = c1.concept_id
        JOIN Concepts c2 ON cd.concept_id = c2.concept_id
        ORDER BY c1.concept_name ASC
    """)
    dependencies = [dict(r) for r in cursor.fetchall()]

    # Units list for dropdown
    cursor.execute("SELECT unit_id, unit_number, unit_name FROM Units ORDER BY unit_number ASC")
    all_units = [dict(r) for r in cursor.fetchall()]

    # Concepts list for dropdown
    cursor.execute("SELECT concept_id, concept_name FROM Concepts ORDER BY concept_name ASC")
    all_concepts = [dict(r) for r in cursor.fetchall()]

    # Topics list for dropdown
    cursor.execute("SELECT topic_id, topic_name FROM Topics ORDER BY topic_name ASC")
    all_topics = [dict(r) for r in cursor.fetchall()]

    # Course details
    cursor.execute("SELECT subject_id, subject_name, code, description FROM Subjects WHERE lecturer_id = ? LIMIT 1", (user["user_id"],))
    subj_row = cursor.fetchone()
    if not subj_row:
        cursor.execute("SELECT subject_id, subject_name, code, description FROM Subjects LIMIT 1")
        subj_row = cursor.fetchone()
    subject = dict(subj_row) if subj_row else None

    conn.close()

    return render_template("lecturer_curriculum.html",
        subject=subject,
        curriculum=curriculum,
        dependencies=dependencies,
        all_units=all_units,
        all_concepts=all_concepts,
        all_topics=all_topics
    )

@app.route("/api/lecturer/add-unit", methods=["POST"])
@role_required("lecturer")
def api_add_unit():
    user = get_current_user()
    data = request.get_json() or {}
    unit_name = data.get("unit_name", "").strip()
    unit_number = data.get("unit_number")

    if not unit_name or not unit_number:
        return jsonify({"error": "Unit name and number required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    subject_id = data.get("subject_id")
    if not subject_id:
        cursor.execute("SELECT subject_id FROM Subjects WHERE lecturer_id = ? LIMIT 1", (user["user_id"],))
        subj = cursor.fetchone()
        if not subj:
            cursor.execute("SELECT subject_id FROM Subjects LIMIT 1")
            subj = cursor.fetchone()
        subject_id = subj["subject_id"] if subj else 1

    cursor.execute("""
        INSERT INTO Units (subject_id, unit_number, unit_name)
        VALUES (?, ?, ?)
    """, (subject_id, unit_number, unit_name))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"success": True, "unit_id": new_id, "unit_name": unit_name})

@app.route("/api/lecturer/add-topic", methods=["POST"])
@role_required("lecturer")
def api_add_topic():

    data = request.get_json() or {}
    unit_id = data.get("unit_id")
    topic_name = data.get("topic_name", "").strip()

    if not unit_id or not topic_name:
        return jsonify({"error": "Unit ID and topic name required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Topics (unit_id, topic_name)
        VALUES (?, ?)
    """, (unit_id, topic_name))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"success": True, "topic_id": new_id, "topic_name": topic_name})

@app.route("/api/lecturer/delete-dependency", methods=["POST"])
@role_required("lecturer")
def api_delete_dependency():

    data = request.get_json() or {}
    dep_id = data.get("dependency_id")

    if not dep_id:
        return jsonify({"error": "Dependency ID required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ConceptDependencies WHERE dependency_id = ?", (dep_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

@app.route("/api/lecturer/add-concept", methods=["POST"])
@role_required("lecturer")
def api_add_concept():

    data = request.get_json() or {}
    topic_id = data.get("topic_id")
    name = data.get("concept_name", "").strip()
    desc = data.get("description", "").strip()
    explanation = data.get("explanation_md", "").strip()
    key_points = data.get("key_points", "").strip()
    code = data.get("code_example", "").strip()

    if not topic_id or not name:
        return jsonify({"error": "Topic and concept name required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Concepts (topic_id, concept_name, description, explanation_md, key_points, code_example)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (topic_id, name, desc, explanation, key_points, code))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"success": True, "concept_id": new_id, "concept_name": name})

@app.route("/api/lecturer/add-dependency", methods=["POST"])
@role_required("lecturer")
def api_add_dependency():

    data = request.get_json() or {}
    target_id = data.get("concept_id")
    prereq_id = data.get("prerequisite_concept_id")

    if not target_id or not prereq_id or target_id == prereq_id:
        return jsonify({"error": "Invalid prerequisite relationship"}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO ConceptDependencies (concept_id, prerequisite_concept_id)
            VALUES (?, ?)
        """, (target_id, prereq_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Dependency already exists"}), 400

@app.route("/lecturer/questions")
@role_required("lecturer")
def lecturer_questions():
    user = get_current_user()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT q.question_id, q.question_text, q.difficulty, q.options_json, q.correct_answer, q.marks,
               c.concept_id, c.concept_name, t.topic_name, u.unit_name
        FROM Questions q
        JOIN Concepts c ON q.concept_id = c.concept_id
        JOIN Topics t ON c.topic_id = t.topic_id
        JOIN Units u ON t.unit_id = u.unit_id
        ORDER BY c.concept_name ASC, q.difficulty ASC
    """)
    raw_qs = cursor.fetchall()

    questions = []
    for r in raw_qs:
        qd = dict(r)
        qd["options"] = json.loads(r["options_json"])
        questions.append(qd)

    cursor.execute("SELECT concept_id, concept_name FROM Concepts ORDER BY concept_name ASC")
    concepts = [dict(r) for r in cursor.fetchall()]

    # Fetch all assessments so lecturer can manage their time durations
    cursor.execute("""
        SELECT assessment_id, title, assessment_type, duration_minutes
        FROM Assessments
        ORDER BY assessment_type ASC, assessment_id ASC
    """)
    assessments = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return render_template("lecturer_questions.html",
        questions=questions,
        concepts=concepts,
        assessments=assessments
    )

@app.route("/api/lecturer/create-question", methods=["POST"])
@role_required("lecturer")
def api_create_question():

    data = request.get_json() or {}
    cid = data.get("concept_id")
    diff = data.get("difficulty")
    qtext = data.get("question_text", "").strip()
    options = data.get("options", [])
    correct = data.get("correct_answer", "").strip()
    expl = data.get("explanation", "").strip()
    marks = data.get("marks", 1)

    if not cid or not diff or not qtext or not correct or len(options) < 2:
        return jsonify({"error": "All fields including at least 2 options and correct answer are required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Questions (concept_id, difficulty, question_text, question_type, options_json, correct_answer, explanation, marks)
        VALUES (?, ?, ?, 'MCQ', ?, ?, ?, ?)
    """, (cid, diff, qtext, json.dumps(options), correct, expl, marks))
    conn.commit()
    new_qid = cursor.lastrowid

    # Automatically attach to active initial assessment
    cursor.execute("SELECT assessment_id FROM Assessments WHERE assessment_type = 'initial' LIMIT 1")
    asm = cursor.fetchone()
    if asm:
        cursor.execute("INSERT OR IGNORE INTO AssessmentQuestions (assessment_id, question_id) VALUES (?, ?)", (asm["assessment_id"], new_qid))
        conn.commit()

    conn.close()

    return jsonify({"success": True, "question_id": new_qid})

@app.route("/api/lecturer/update-assessment-duration", methods=["POST"])
@role_required("lecturer")
def api_update_assessment_duration():
    """Allow lecturers to set/update the time limit (in minutes) for any assessment."""
    data = request.get_json() or {}
    assessment_id = data.get("assessment_id")
    duration = data.get("duration_minutes")

    if not assessment_id or duration is None:
        return jsonify({"error": "assessment_id and duration_minutes are required"}), 400

    try:
        duration = int(duration)
        if duration < 1 or duration > 300:
            return jsonify({"error": "Duration must be between 1 and 300 minutes"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "duration_minutes must be a valid integer"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Assessments SET duration_minutes = ? WHERE assessment_id = ?
    """, (duration, assessment_id))
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Assessment not found"}), 404
    conn.commit()
    conn.close()

    return jsonify({"success": True, "assessment_id": assessment_id, "duration_minutes": duration})

# ----------------- ENTRY POINT -----------------

if __name__ == "__main__":
    init_db()
    print("Cognimap AI server starting on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)

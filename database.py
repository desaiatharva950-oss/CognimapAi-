"""
Cognimap AI - Database Initialization and Relational Schema
Implements Section 14 of guidelines.md
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "cognimap.db")

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def init_db(seed_if_empty: bool = True):
    conn = get_db()
    cursor = conn.cursor()

    # 1. Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('student', 'lecturer', 'admin')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Subjects
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Subjects (
        subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_name TEXT NOT NULL,
        code TEXT NOT NULL,
        description TEXT,
        lecturer_id INTEGER,
        FOREIGN KEY (lecturer_id) REFERENCES Users(user_id) ON DELETE SET NULL
    );
    """)

    # 3. Units
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Units (
        unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL,
        unit_number INTEGER NOT NULL,
        unit_name TEXT NOT NULL,
        FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id) ON DELETE CASCADE
    );
    """)

    # 4. Topics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Topics (
        topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
        unit_id INTEGER NOT NULL,
        topic_name TEXT NOT NULL,
        FOREIGN KEY (unit_id) REFERENCES Units(unit_id) ON DELETE CASCADE
    );
    """)

    # 5. Concepts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Concepts (
        concept_id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id INTEGER NOT NULL,
        concept_name TEXT NOT NULL,
        description TEXT,
        explanation_md TEXT,
        key_points TEXT,
        code_example TEXT,
        FOREIGN KEY (topic_id) REFERENCES Topics(topic_id) ON DELETE CASCADE
    );
    """)

    # 6. ConceptDependencies (Prerequisite Relationships)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ConceptDependencies (
        dependency_id INTEGER PRIMARY KEY AUTOINCREMENT,
        concept_id INTEGER NOT NULL,
        prerequisite_concept_id INTEGER NOT NULL,
        dependency_strength REAL DEFAULT 1.0,
        FOREIGN KEY (concept_id) REFERENCES Concepts(concept_id) ON DELETE CASCADE,
        FOREIGN KEY (prerequisite_concept_id) REFERENCES Concepts(concept_id) ON DELETE CASCADE,
        UNIQUE(concept_id, prerequisite_concept_id)
    );
    """)

    # 7. Questions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Questions (
        question_id INTEGER PRIMARY KEY AUTOINCREMENT,
        concept_id INTEGER NOT NULL,
        difficulty TEXT NOT NULL CHECK(difficulty IN ('Easy', 'Medium', 'Hard')),
        question_text TEXT NOT NULL,
        question_type TEXT NOT NULL DEFAULT 'MCQ',
        options_json TEXT NOT NULL,
        correct_answer TEXT NOT NULL,
        explanation TEXT,
        marks INTEGER DEFAULT 1,
        FOREIGN KEY (concept_id) REFERENCES Concepts(concept_id) ON DELETE CASCADE
    );
    """)

    # 8. Assessments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Assessments (
        assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL,
        lecturer_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        assessment_type TEXT NOT NULL DEFAULT 'initial' CHECK(assessment_type IN ('initial', 'followup')),
        target_concept_ids TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        duration_minutes INTEGER DEFAULT 30,
        FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id) ON DELETE CASCADE,
        FOREIGN KEY (lecturer_id) REFERENCES Users(user_id) ON DELETE CASCADE
    );
    """)

    # 9. AssessmentQuestions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS AssessmentQuestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assessment_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        FOREIGN KEY (assessment_id) REFERENCES Assessments(assessment_id) ON DELETE CASCADE,
        FOREIGN KEY (question_id) REFERENCES Questions(question_id) ON DELETE CASCADE,
        UNIQUE(assessment_id, question_id)
    );
    """)

    # 10. StudentAttempts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS StudentAttempts (
        attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        assessment_id INTEGER NOT NULL,
        score REAL NOT NULL,
        max_score REAL NOT NULL,
        percentage REAL NOT NULL,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        time_taken_seconds INTEGER DEFAULT 0,
        FOREIGN KEY (student_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (assessment_id) REFERENCES Assessments(assessment_id) ON DELETE CASCADE
    );
    """)

    # 11. StudentAnswers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS StudentAnswers (
        answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        attempt_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        selected_answer TEXT NOT NULL,
        correctness INTEGER NOT NULL CHECK(correctness IN (0, 1)),
        marks_awarded REAL NOT NULL,
        FOREIGN KEY (attempt_id) REFERENCES StudentAttempts(attempt_id) ON DELETE CASCADE,
        FOREIGN KEY (question_id) REFERENCES Questions(question_id) ON DELETE CASCADE
    );
    """)

    # 12. ConceptPerformance
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ConceptPerformance (
        performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        concept_id INTEGER NOT NULL,
        assessment_id INTEGER NOT NULL,
        score REAL NOT NULL,
        total_questions INTEGER DEFAULT 0,
        correct_questions INTEGER DEFAULT 0,
        status TEXT NOT NULL CHECK(status IN ('Strong', 'Needs Improvement', 'Weak')),
        assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (concept_id) REFERENCES Concepts(concept_id) ON DELETE CASCADE,
        FOREIGN KEY (assessment_id) REFERENCES Assessments(assessment_id) ON DELETE CASCADE,
        UNIQUE(student_id, concept_id, assessment_id)
    );
    """)

    # Migration: add UNIQUE index if table already exists without it
    try:
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_cp_unique
            ON ConceptPerformance(student_id, concept_id, assessment_id)
        """)
    except Exception:
        pass

    # Migration: deduplicate existing ConceptPerformance rows (keep highest score per unique tuple)
    cursor.execute("""
        DELETE FROM ConceptPerformance
        WHERE performance_id NOT IN (
            SELECT MAX(performance_id)
            FROM ConceptPerformance
            GROUP BY student_id, concept_id, assessment_id
        )
    """)

    # 13. LearningPaths
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LearningPaths (
        path_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        assessment_id INTEGER NOT NULL,
        concept_id INTEGER NOT NULL,
        priority INTEGER NOT NULL,
        recommendation_reason TEXT NOT NULL,
        is_prerequisite_gap INTEGER DEFAULT 0,
        target_weak_concept_id INTEGER,
        is_completed INTEGER DEFAULT 0,
        FOREIGN KEY (student_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (assessment_id) REFERENCES Assessments(assessment_id) ON DELETE CASCADE,
        FOREIGN KEY (concept_id) REFERENCES Concepts(concept_id) ON DELETE CASCADE
    );
    """)

    # 14. FollowUpAssessments & Improvement
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS FollowUpAssessments (
        followup_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        initial_assessment_id INTEGER NOT NULL,
        followup_attempt_id INTEGER NOT NULL,
        previous_overall_score REAL NOT NULL,
        new_overall_score REAL NOT NULL,
        overall_improvement REAL NOT NULL,
        concept_improvements_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (initial_assessment_id) REFERENCES Assessments(assessment_id) ON DELETE CASCADE,
        FOREIGN KEY (followup_attempt_id) REFERENCES StudentAttempts(attempt_id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

    if seed_if_empty:
        try:
            import seed_data
            seed_data.seed(wipe=False)
        except Exception as e:
            print(f"Notice: Baseline database initialization note: {e}")

if __name__ == "__main__":
    init_db()
    print("Database schema created successfully.")

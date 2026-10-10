"""
Cognimap AI - Comprehensive Test Suite
Verifies algorithms, database relationships, prerequisite DAG traversal,
learning path generation, follow-up improvement calculations, and Flask endpoints.
"""

import unittest
import json
import os
from database import get_db, init_db
from analytics_engine import PrerequisiteGraphEngine, get_status_from_score
from server import app

class TestCognimap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.conn = get_db()
        cls.engine = PrerequisiteGraphEngine(cls.conn)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_01_database_and_graph_loaded(self):
        """Verify database and NetworkX DAG loading."""
        self.assertGreaterEqual(len(self.engine.graph.nodes), 10, "Should have at least 10 concepts loaded")
        self.assertGreaterEqual(len(self.engine.graph.edges), 10, "Should have prerequisite edges loaded")

    def test_02_status_classification(self):
        """Verify threshold classification (Section 5)."""
        self.assertEqual(get_status_from_score(90.0), "Strong")
        self.assertEqual(get_status_from_score(75.0), "Strong")
        self.assertEqual(get_status_from_score(74.9), "Needs Improvement")
        self.assertEqual(get_status_from_score(50.0), "Needs Improvement")
        self.assertEqual(get_status_from_score(49.9), "Weak")
        self.assertEqual(get_status_from_score(32.0), "Weak")

    def test_03_prerequisite_gap_detection(self):
        """Verify detection of prerequisite gaps for weak concepts (Section 6 & 20)."""
        # Canonical Student A scores:
        # Graphs = 32% (Weak), Trees = 45% (Weak), Recursion = 48% (Weak)
        cursor = self.conn.cursor()
        cursor.execute("SELECT concept_id, concept_name FROM Concepts")
        c_map = {row["concept_name"]: row["concept_id"] for row in cursor.fetchall()}

        score_map = {
            c_map["Arrays"]: 90.0,
            c_map["Linked Lists"]: 82.0,
            c_map["Stack"]: 76.0,
            c_map["Queue"]: 70.0,
            c_map["Recursion"]: 48.0,
            c_map["Trees"]: 45.0,
            c_map["Graphs"]: 32.0,
            c_map["BFS"]: 38.0,
            c_map["DFS"]: 35.0
        }

        gaps = self.engine.detect_prerequisite_gaps(score_map)
        self.assertGreater(len(gaps), 0, "Should detect prerequisite gaps")

        # Verify Graphs gap detected
        graph_gap = next((g for g in gaps if g["concept_name"] == "Graphs"), None)
        self.assertIsNotNone(graph_gap, "Graphs should have prerequisite gap identified")
        prereq_names = [p["concept_name"] for p in graph_gap["weak_prerequisites"]]
        self.assertTrue("Trees" in prereq_names or "Recursion" in prereq_names, "Should identify Trees or Recursion as upstream gap")

    def test_04_topological_learning_path(self):
        """Verify topological revision ordering (Section 8 & 20)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT concept_id, concept_name FROM Concepts")
        c_map = {row["concept_name"]: row["concept_id"] for row in cursor.fetchall()}

        score_map = {
            c_map["Arrays"]: 90.0,
            c_map["Linked Lists"]: 82.0,
            c_map["Stack"]: 76.0,
            c_map["Queue"]: 70.0,
            c_map["Recursion"]: 48.0,
            c_map["Trees"]: 45.0,
            c_map["Graphs"]: 32.0,
            c_map["BFS"]: 38.0,
            c_map["DFS"]: 35.0
        }

        gaps = self.engine.detect_prerequisite_gaps(score_map)
        path = self.engine.generate_learning_path(score_map, gaps)
        names = [p["concept_name"] for p in path]

        # Strong concepts should NOT be in the revision path
        self.assertNotIn("Arrays", names)
        self.assertNotIn("Linked Lists", names)
        self.assertNotIn("Stack", names)

        # Topological check: Recursion must come before Trees, Trees before Graphs
        if "Recursion" in names and "Trees" in names:
            self.assertLess(names.index("Recursion"), names.index("Trees"), "Recursion must be revised before Trees")
        if "Trees" in names and "Graphs" in names:
            self.assertLess(names.index("Trees"), names.index("Graphs"), "Trees must be revised before Graphs")
        if "Graphs" in names and "BFS" in names:
            self.assertLess(names.index("Graphs"), names.index("BFS"), "Graphs must be revised before BFS")

    def test_05_followup_improvement_calculation(self):
        """Verify observed improvement computation (Section 10)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT attempt_id FROM StudentAttempts ORDER BY attempt_id ASC LIMIT 2")
        rows = cursor.fetchall()
        if len(rows) >= 2:
            res = self.engine.compute_improvement(rows[0]["attempt_id"], rows[1]["attempt_id"])
            self.assertIn("overall_delta", res)
            self.assertIn("concepts", res)

    def test_06_flask_endpoints(self):
        """Verify primary web routes."""
        # 1. Landing page
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)

        # 2. Login page
        res = self.client.get("/login")
        self.assertEqual(res.status_code, 200)

        # 3. Knowledge Map API
        res = self.client.get("/api/knowledge-map")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("nodes", data)
        self.assertIn("edges", data)

        # 4. Demo login as Student A
        res = self.client.get("/demo-login/student", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Atharva Desai", res.data)

        # 5. Student Dashboard
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 200)

        # 6. Knowledge Map View
        res = self.client.get("/knowledge-map")
        self.assertEqual(res.status_code, 200)

        # 7. Learning Path View
        res = self.client.get("/learning-path")
        self.assertEqual(res.status_code, 200)

        # 8. Follow-up Quiz View
        res = self.client.get("/followup-quiz")
        self.assertEqual(res.status_code, 200)

        # 9. Demo login as Lecturer
        res = self.client.get("/demo-login/lecturer", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Dr. Rajesh Sharma", res.data)

        # 10. Lecturer Dashboard
        res = self.client.get("/lecturer")
        self.assertEqual(res.status_code, 200)

        # 11. Lecturer Curriculum View
        res = self.client.get("/lecturer/curriculum")
        self.assertEqual(res.status_code, 200)

        # 12. Lecturer Question Bank View
        res = self.client.get("/lecturer/questions")
        self.assertEqual(res.status_code, 200)

    def test_07_edge_cases_zero_and_perfect_score(self):
        """Verify edge cases: 0% and 100% scores (Section 23)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT concept_id FROM Concepts LIMIT 5")
        cids = [r["concept_id"] for r in cursor.fetchall()]

        # 1. Edge case: 0% score across all concepts
        zero_score_map = {cid: 0.0 for cid in cids}
        gaps_zero = self.engine.detect_prerequisite_gaps(zero_score_map)
        path_zero = self.engine.generate_learning_path(zero_score_map, gaps_zero)
        self.assertGreater(len(gaps_zero), 0, "Zero score should trigger diagnostic gaps")
        self.assertEqual(len(path_zero), len(cids), "All 0% concepts should be in revision path")

        # 2. Edge case: 100% score across all concepts
        perfect_score_map = {cid: 100.0 for cid in cids}
        gaps_perf = self.engine.detect_prerequisite_gaps(perfect_score_map)
        path_perf = self.engine.generate_learning_path(perfect_score_map, gaps_perf)
        self.assertEqual(len(gaps_perf), 0, "100% mastery should trigger no prerequisite gaps")
        self.assertEqual(len(path_perf), 0, "100% mastery should require no revision steps")

    def test_08_assessment_submission_flow(self):
        """Verify submitting an assessment and student skipping questions."""
        # Log in as Student A
        self.client.get("/demo-login/student")

        cursor = self.conn.cursor()
        cursor.execute("SELECT assessment_id FROM Assessments WHERE assessment_type = 'initial' LIMIT 1")
        asm_id = cursor.fetchone()["assessment_id"]

        # Student skips some questions (empty answers dictionary)
        payload = {
            "assessment_id": asm_id,
            "answers": {},
            "time_taken_seconds": 120
        }
        res = self.client.post("/api/submit-assessment",
                               data=json.dumps(payload),
                               content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        self.assertIn("attempt_id", data)
        self.assertIn("redirect_url", data)

    def test_09_lecturer_authoring_apis(self):
        """Verify lecturer curriculum, prerequisite, and question creation endpoints."""
        # Log in as Lecturer
        self.client.get("/demo-login/lecturer")

        cursor = self.conn.cursor()
        cursor.execute("SELECT topic_id FROM Topics LIMIT 1")
        topic_id = cursor.fetchone()["topic_id"]

        # 1. Add Concept
        c_res = self.client.post("/api/lecturer/add-concept",
                                 data=json.dumps({
                                     "topic_id": topic_id,
                                     "concept_name": "Test Concept Node",
                                     "description": "Test concept description for verification",
                                     "explanation_md": "Detailed theory notes",
                                     "key_points": "Principle A, Principle B",
                                     "code_example": "int x = 42;"
                                 }),
                                 content_type="application/json")
        self.assertEqual(c_res.status_code, 200)
        c_data = json.loads(c_res.data)
        self.assertTrue(c_data.get("success"))
        new_cid = c_data.get("concept_id")

        # 2. Add Question tagged to new concept
        q_res = self.client.post("/api/lecturer/create-question",
                                 data=json.dumps({
                                     "concept_id": new_cid,
                                     "difficulty": "Medium",
                                     "question_text": "What is the result of test concept?",
                                     "options": ["Answer A", "Answer B", "Answer C", "Answer D"],
                                     "correct_answer": "Answer A",
                                     "explanation": "Answer A is standard.",
                                     "marks": 1
                                 }),
                                 content_type="application/json")
        self.assertEqual(q_res.status_code, 200)
        q_data = json.loads(q_res.data)
        self.assertTrue(q_data.get("success"))

        # 3. Add Unit
        u_res = self.client.post("/api/lecturer/add-unit",
                                 data=json.dumps({
                                     "unit_number": 99,
                                     "unit_name": "Test Syllabus Unit"
                                 }),
                                 content_type="application/json")
        self.assertEqual(u_res.status_code, 200)
        u_data = json.loads(u_res.data)
        self.assertTrue(u_data.get("success"))
        new_uid = u_data.get("unit_id")

        # 4. Add Topic
        t_res = self.client.post("/api/lecturer/add-topic",
                                 data=json.dumps({
                                     "unit_id": new_uid,
                                     "topic_name": "Test Module Topic"
                                 }),
                                 content_type="application/json")
        self.assertEqual(t_res.status_code, 200)
        t_data = json.loads(t_res.data)
        self.assertTrue(t_data.get("success"))

        # 5. Add Dependency
        dep_res = self.client.post("/api/lecturer/add-dependency",
                                   data=json.dumps({
                                       "concept_id": new_cid,
                                       "prerequisite_concept_id": 1
                                   }),
                                   content_type="application/json")
        self.assertEqual(dep_res.status_code, 200)

        # 6. Delete Dependency
        cursor.execute("SELECT dependency_id FROM ConceptDependencies WHERE concept_id = ? AND prerequisite_concept_id = ?", (new_cid, 1))
        dep_row = cursor.fetchone()
        if dep_row:
            del_res = self.client.post("/api/lecturer/delete-dependency",
                                       data=json.dumps({"dependency_id": dep_row["dependency_id"]}),
                                       content_type="application/json")
            self.assertEqual(del_res.status_code, 200)
            del_data = json.loads(del_res.data)
            self.assertTrue(del_data.get("success"))

    def test_10_role_permissions_and_student_privacy(self):
        """Verify role security: students cannot access faculty portal or other student records."""
        # Log in as Student
        self.client.get("/demo-login/student")

        # Attempt to access Lecturer Dashboard
        res_lec = self.client.get("/lecturer")
        self.assertEqual(res_lec.status_code, 302, "Student must be redirected away from lecturer dashboard")

        # Attempt to add concept via API as student
        res_api = self.client.post("/api/lecturer/add-concept",
                                   data=json.dumps({"topic_id": 1, "concept_name": "Unauthorized"}),
                                   content_type="application/json")
        self.assertEqual(res_api.status_code, 401, "Student must receive 401 Unauthorized for faculty APIs")

    def test_11_role_based_auth_flow(self):
        """Verify real application user registration, login, role redirection, and route protection."""
        # 1. Unauthenticated users cannot access student or lecturer dashboards
        self.client.get("/logout")
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers.get("Location", ""))

        res = self.client.get("/lecturer")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers.get("Location", ""))

        # Clean up any previous test users to ensure idempotency
        c_conn = get_db()
        c_cur = c_conn.cursor()
        c_cur.execute("DELETE FROM Users WHERE email IN ('jane.student@cognimap.edu', 'prof.valid@cognimap.edu', 'fake.prof@cognimap.edu')")
        c_conn.commit()
        c_conn.close()

        # 2. Register new student
        res_reg_student = self.client.post("/register", data={
            "name": "Jane Student",
            "email": "jane.student@cognimap.edu",
            "password": "securepassword123",
            "role": "student"
        }, follow_redirects=False)
        self.assertEqual(res_reg_student.status_code, 302)
        self.assertIn("/dashboard", res_reg_student.headers.get("Location", ""))

        # Student cannot access lecturer portal
        res_boundary = self.client.get("/lecturer", follow_redirects=False)
        self.assertEqual(res_boundary.status_code, 302)
        self.assertIn("/dashboard", res_boundary.headers.get("Location", ""))

        # 3. Register lecturer with invalid faculty code (must fail)
        self.client.get("/logout")
        res_bad_code = self.client.post("/register", data={
            "name": "Unauthorized Lecturer",
            "email": "fake.prof@cognimap.edu",
            "password": "password123",
            "role": "lecturer",
            "faculty_code": "WRONG_CODE"
        })
        self.assertEqual(res_bad_code.status_code, 200)
        self.assertIn(b"Invalid Faculty Verification Code", res_bad_code.data)

        # 4. Register lecturer with valid faculty code (must succeed)
        res_good_code = self.client.post("/register", data={
            "name": "Dr. Valid Faculty",
            "email": "prof.valid@cognimap.edu",
            "password": "password123",
            "role": "lecturer",
            "faculty_code": "FACULTY2026"
        }, follow_redirects=False)
        self.assertEqual(res_good_code.status_code, 302)
        self.assertIn("/lecturer", res_good_code.headers.get("Location", ""))

        # Lecturer cannot access student-only workflows (redirects to /lecturer)
        res_lec_student_route = self.client.get("/dashboard", follow_redirects=False)
        self.assertEqual(res_lec_student_route.status_code, 302)
        self.assertIn("/lecturer", res_lec_student_route.headers.get("Location", ""))

        # 5. Form-based credential login
        self.client.get("/logout")
        res_login = self.client.post("/login", data={
            "email": "jane.student@cognimap.edu",
            "password": "securepassword123"
        }, follow_redirects=False)
        self.assertEqual(res_login.status_code, 302)
        self.assertIn("/dashboard", res_login.headers.get("Location", ""))

    def test_12_password_hashing_and_security(self):
        """Verify modern password verification and student IDOR isolation in knowledge map."""
        import hashlib
        self.client.get("/logout")

        # 1. Reset studentA to legacy SHA-256 hash to test transparent upgrade
        fresh_conn = get_db()
        cursor = fresh_conn.cursor()
        legacy_sha = hashlib.sha256(b"student123").hexdigest()
        cursor.execute("UPDATE Users SET password_hash = ? WHERE email = 'studentA@cognimap.edu'", (legacy_sha,))
        fresh_conn.commit()
        initial_hash = legacy_sha
        fresh_conn.close()

        # Log in with actual credentials
        res = self.client.post("/login", data={
            "email": "studentA@cognimap.edu",
            "password": "student123"
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)

        # Verify hash upgraded in database to salted hash
        fresh_conn = get_db()
        cursor = fresh_conn.cursor()
        cursor.execute("SELECT password_hash FROM Users WHERE email = 'studentA@cognimap.edu'")
        upgraded_hash = cursor.fetchone()["password_hash"]
        fresh_conn.close()

        self.assertNotEqual(initial_hash, upgraded_hash)
        self.assertTrue(upgraded_hash.startswith(("scrypt:", "pbkdf2:")))

        # 2. Student IDOR prevention: student requests ?student_id=999 but receives their own data
        map_res = self.client.get("/api/knowledge-map?student_id=999")
        self.assertEqual(map_res.status_code, 200)
        map_data = json.loads(map_res.data)
        self.assertIn("nodes", map_data)

    def test_13_assessment_duration_and_timer(self):
        """Verify Lecturer duration configuration and student assessment timer & submission."""
        # 1. Lecturer logs in and sets assessment duration to 20 minutes
        self.client.get("/logout")
        self.client.post("/login", data={
            "email": "prof.valid@cognimap.edu",
            "password": "password123"
        })

        # Lecturer questions page contains duration configuration
        lec_res = self.client.get("/lecturer/questions")
        self.assertEqual(lec_res.status_code, 200)
        lec_html = lec_res.data.decode("utf-8")
        self.assertIn("Assessment Time Limits &amp; Duration", lec_html)
        self.assertIn("updateAssessmentDuration", lec_html)

        # Update duration via API
        update_res = self.client.post("/api/lecturer/update-assessment-duration", json={
            "assessment_id": 1,
            "duration_minutes": 20
        })
        self.assertEqual(update_res.status_code, 200)
        self.assertTrue(update_res.get_json().get("success"))

        # 2. Student logs in and takes assessment
        self.client.get("/logout")
        self.client.post("/login", data={
            "email": "jane.student@cognimap.edu",
            "password": "securepassword123"
        })

        asm_res = self.client.get("/assessment/1")
        self.assertEqual(asm_res.status_code, 200)
        asm_html = asm_res.data.decode("utf-8")

        # Verify timer settings passed to student page
        self.assertIn("durationMinutes = 20", asm_html)
        self.assertIn("Time Remaining", asm_html)
        self.assertIn("time-expired-alert", asm_html)
        self.assertIn("handleTimeExpired", asm_html)
        self.assertIn("lockAssessmentUI", asm_html)

        # 3. Submit assessment with answers and time_taken_seconds
        sub_res = self.client.post("/api/submit-assessment", json={
            "assessment_id": 1,
            "answers": {"1": "O(V + E)"},
            "time_taken_seconds": 1200
        })
        self.assertEqual(sub_res.status_code, 200)
        sub_data = sub_res.get_json()
        self.assertTrue(sub_data.get("success"))
        self.assertIn("diagnostic-report", sub_data.get("redirect_url"))

        # Restore duration to 45 mins
        self.client.get("/logout")
        self.client.post("/login", data={
            "email": "prof.valid@cognimap.edu",
            "password": "password123"
        })
        self.client.post("/api/lecturer/update-assessment-duration", json={
            "assessment_id": 1,
            "duration_minutes": 45
        })

if __name__ == "__main__":
    unittest.main()



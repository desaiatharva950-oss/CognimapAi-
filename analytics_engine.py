"""
Cognimap AI - Intelligent Prerequisite Graph Analysis & Recommendation Engine
Uses NetworkX to model concept DAGs, detect prerequisite gaps, and synthesize
personalized, topologically-sorted learning paths with explainable diagnostics.
"""

import networkx as nx
import json
from typing import Dict, List, Any, Optional

# Configurable thresholds as mandated by Section 5
STRONG_THRESHOLD = 75.0      # >= 75% -> Strong (Green)
WEAK_THRESHOLD = 50.0        # < 50% -> Weak (Red); 50% - 74% -> Needs Improvement (Yellow)

def get_status_from_score(score: float) -> str:
    """Classifies score based on configurable thresholds."""
    if score >= STRONG_THRESHOLD:
        return "Strong"
    elif score >= WEAK_THRESHOLD:
        return "Needs Improvement"
    else:
        return "Weak"

class PrerequisiteGraphEngine:
    def __init__(self, db_conn):
        self.conn = db_conn
        self.graph = nx.DiGraph()
        self.load_graph()

    def load_graph(self):
        """Loads concepts and prerequisite relationships into a NetworkX DiGraph."""
        self.graph.clear()
        cursor = self.conn.cursor()

        # Load all concepts as nodes
        cursor.execute("""
            SELECT c.concept_id, c.concept_name, c.description, c.explanation_md,
                   c.key_points, c.code_example, t.topic_name, u.unit_name, u.unit_number
            FROM Concepts c
            JOIN Topics t ON c.topic_id = t.topic_id
            JOIN Units u ON t.unit_id = u.unit_id
        """)
        for row in cursor.fetchall():
            self.graph.add_node(
                row["concept_id"],
                id=row["concept_id"],
                name=row["concept_name"],
                description=row["description"] or "",
                explanation=row["explanation_md"] or "",
                key_points=row["key_points"] or "",
                code_example=row["code_example"] or "",
                topic=row["topic_name"],
                unit=row["unit_name"],
                unit_number=row["unit_number"]
            )

        # Load directed prerequisite edges: Prerequisite -> Target Concept
        cursor.execute("SELECT concept_id, prerequisite_concept_id FROM ConceptDependencies")
        for row in cursor.fetchall():
            target_id = row["concept_id"]
            prereq_id = row["prerequisite_concept_id"]
            if prereq_id in self.graph and target_id in self.graph:
                # Directed edge: prerequisite -> concept
                self.graph.add_edge(prereq_id, target_id)

    def analyze_attempt(self, attempt_id: int) -> Dict[str, Any]:
        """
        Analyzes a student attempt:
        1. Computes concept-wise scores, topic-wise, unit-wise, difficulty-wise
        2. Performs prerequisite gap detection
        3. Generates personalized learning path
        4. Saves concept performance & learning path to DB
        """
        cursor = self.conn.cursor()

        # Fetch attempt details
        cursor.execute("SELECT student_id, assessment_id FROM StudentAttempts WHERE attempt_id = ?", (attempt_id,))
        attempt_row = cursor.fetchone()
        if not attempt_row:
            return {"error": "Attempt not found"}

        student_id = attempt_row["student_id"]
        assessment_id = attempt_row["assessment_id"]

        # Fetch all questions and student answers for this attempt
        cursor.execute("""
            SELECT q.question_id, q.concept_id, q.difficulty, q.marks,
                   a.selected_answer, a.correctness, a.marks_awarded,
                   c.concept_name, t.topic_name, u.unit_name, u.unit_number
            FROM StudentAnswers a
            JOIN Questions q ON a.question_id = q.question_id
            JOIN Concepts c ON q.concept_id = c.concept_id
            JOIN Topics t ON c.topic_id = t.topic_id
            JOIN Units u ON t.unit_id = u.unit_id
            WHERE a.attempt_id = ?
        """, (attempt_id,))
        answers = cursor.fetchall()

        if not answers:
            return {"error": "No answers found for attempt"}

        # Calculate metrics
        concept_stats = {}
        topic_stats = {}
        unit_stats = {}
        diff_stats = {"Easy": {"earned": 0, "total": 0}, "Medium": {"earned": 0, "total": 0}, "Hard": {"earned": 0, "total": 0}}
        total_earned = 0
        total_possible = 0

        for ans in answers:
            cid = ans["concept_id"]
            cname = ans["concept_name"]
            marks_awarded = ans["marks_awarded"]
            marks_total = ans["marks"]
            diff = ans["difficulty"]
            topic = ans["topic_name"]
            unit = f"Unit {ans['unit_number']}: {ans['unit_name']}"

            total_earned += marks_awarded
            total_possible += marks_total

            # Concept
            if cid not in concept_stats:
                concept_stats[cid] = {"id": cid, "name": cname, "earned": 0, "total": 0, "questions_count": 0, "correct_count": 0}
            concept_stats[cid]["earned"] += marks_awarded
            concept_stats[cid]["total"] += marks_total
            concept_stats[cid]["questions_count"] += 1
            if ans["correctness"] == 1:
                concept_stats[cid]["correct_count"] += 1

            # Topic
            if topic not in topic_stats:
                topic_stats[topic] = {"earned": 0, "total": 0}
            topic_stats[topic]["earned"] += marks_awarded
            topic_stats[topic]["total"] += marks_total

            # Unit
            if unit not in unit_stats:
                unit_stats[unit] = {"earned": 0, "total": 0}
            unit_stats[unit]["earned"] += marks_awarded
            unit_stats[unit]["total"] += marks_total

            # Difficulty
            if diff in diff_stats:
                diff_stats[diff]["earned"] += marks_awarded
                diff_stats[diff]["total"] += marks_total

        # Format Concept Scores & Classify Status
        concepts_analyzed = []
        concept_score_map = {} # cid -> score

        for cid, data in concept_stats.items():
            pct = round((data["earned"] / data["total"]) * 100, 1) if data["total"] > 0 else 0.0
            status = get_status_from_score(pct)
            concept_score_map[cid] = pct

            concepts_analyzed.append({
                "concept_id": cid,
                "concept_name": data["name"],
                "score": pct,
                "status": status,
                "total_questions": data["questions_count"],
                "correct_questions": data["correct_count"]
            })

            # Upsert into ConceptPerformance — one row per (student, concept, assessment)
            cursor.execute("""
                INSERT INTO ConceptPerformance (student_id, concept_id, assessment_id, score, total_questions, correct_questions, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_id, concept_id, assessment_id) DO UPDATE SET
                    score=excluded.score,
                    total_questions=excluded.total_questions,
                    correct_questions=excluded.correct_questions,
                    status=excluded.status,
                    assessed_at=CURRENT_TIMESTAMP
            """, (student_id, cid, assessment_id, pct, data["questions_count"], data["correct_count"], status))

        overall_pct = round((total_earned / total_possible) * 100, 1) if total_possible > 0 else 0.0

        # Update attempt overall score
        cursor.execute("""
            UPDATE StudentAttempts
            SET score = ?, max_score = ?, percentage = ?
            WHERE attempt_id = ?
        """, (total_earned, total_possible, overall_pct, attempt_id))

        # Perform Prerequisite Gap Analysis
        prereq_analysis = self.detect_prerequisite_gaps(concept_score_map)

        # Generate Personalized Learning Path
        learning_path = self.generate_learning_path(concept_score_map, prereq_analysis)

        # Save Learning Path to DB
        cursor.execute("DELETE FROM LearningPaths WHERE student_id = ? AND assessment_id = ?", (student_id, assessment_id))
        for idx, step in enumerate(learning_path):
            cursor.execute("""
                INSERT INTO LearningPaths (student_id, assessment_id, concept_id, priority, recommendation_reason, is_prerequisite_gap, target_weak_concept_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (student_id, assessment_id, step["concept_id"], idx + 1, step["reason"], 1 if step["is_prerequisite_gap"] else 0, step.get("target_weak_concept_id")))

        # Deduplicate: each concept appears only once for this student (keep latest)
        cursor.execute("""
            DELETE FROM LearningPaths
            WHERE student_id = ? AND path_id NOT IN (
                SELECT MAX(path_id) FROM LearningPaths
                WHERE student_id = ?
                GROUP BY concept_id
            )
        """, (student_id, student_id))

        self.conn.commit()

        # Format Topic, Unit, Diff breakdowns
        topics_formatted = [{"topic": k, "percentage": round((v["earned"] / v["total"]) * 100, 1) if v["total"] > 0 else 0} for k, v in topic_stats.items()]
        units_formatted = [{"unit": k, "percentage": round((v["earned"] / v["total"]) * 100, 1) if v["total"] > 0 else 0} for k, v in unit_stats.items()]
        diff_formatted = [{"difficulty": k, "percentage": round((v["earned"] / v["total"]) * 100, 1) if v["total"] > 0 else 0} for k, v in diff_stats.items()]

        return {
            "overall_score": overall_pct,
            "total_earned": total_earned,
            "total_possible": total_possible,
            "concept_performance": concepts_analyzed,
            "topic_performance": topics_formatted,
            "unit_performance": units_formatted,
            "difficulty_performance": diff_formatted,
            "prerequisite_analysis": prereq_analysis,
            "learning_path": learning_path
        }

    def detect_prerequisite_gaps(self, concept_score_map: Dict[int, float]) -> List[Dict[str, Any]]:
        """
        For weak and needs-improvement concepts, traverses upstream prerequisite dependencies in the DAG.
        Identifies foundational concepts that are also sub-threshold.
        Generates academically defensible, explainable diagnostic findings.
        """
        findings = []

        # Find concepts that are weak (< 50%) or needs improvement (50-74%)
        weak_cids = [cid for cid, score in concept_score_map.items() if score < WEAK_THRESHOLD]
        ni_cids = [cid for cid, score in concept_score_map.items() if WEAK_THRESHOLD <= score < STRONG_THRESHOLD]

        target_cids = weak_cids + ni_cids

        for cid in target_cids:
            if cid not in self.graph:
                continue

            target_name = self.graph.nodes[cid].get("name", f"Concept {cid}")
            target_score = concept_score_map.get(cid, 0.0)

            # Find all upstream ancestors (prerequisites) using NetworkX
            try:
                ancestors = nx.ancestors(self.graph, cid)
            except Exception:
                ancestors = set()

            weak_prereqs = []
            for anc in ancestors:
                anc_score = concept_score_map.get(anc)
                anc_name = self.graph.nodes[anc].get("name", f"Concept {anc}")
                if anc_score is not None and anc_score < STRONG_THRESHOLD:
                    weak_prereqs.append({
                        "concept_id": anc,
                        "concept_name": anc_name,
                        "score": anc_score,
                        "status": get_status_from_score(anc_score)
                    })

            if weak_prereqs:
                prereq_names = [f"{p['concept_name']} ({p['score']}%)" for p in weak_prereqs]
                names_str = ", ".join(prereq_names)

                finding_text = (
                    f"Performance in '{target_name}' ({target_score}%) appears to be affected by "
                    f"foundational gaps in prerequisite concepts: {names_str}. "
                    f"Mastering these foundational concepts first is recommended before re-attempting {target_name}."
                )

                findings.append({
                    "concept_id": cid,
                    "concept_name": target_name,
                    "concept_score": target_score,
                    "concept_status": get_status_from_score(target_score),
                    "weak_prerequisites": weak_prereqs,
                    "explanation": finding_text
                })
            elif target_score < WEAK_THRESHOLD:
                findings.append({
                    "concept_id": cid,
                    "concept_name": target_name,
                    "concept_score": target_score,
                    "concept_status": "Weak",
                    "weak_prerequisites": [],
                    "explanation": f"Performance in '{target_name}' ({target_score}%) is weak, but all tested prerequisites show adequate mastery. Targeted practice on {target_name} core mechanics is recommended."
                })

        return findings

    def generate_learning_path(self, concept_score_map: Dict[int, float], prereq_analysis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Synthesizes a personalized, topologically-sorted revision path:
        1. Identifies all concepts needing attention (Weak, Needs Improvement, and prerequisite gaps).
        2. Sorts them topologically according to the concept dependency DAG.
           Foundational prerequisites come FIRST, dependent higher-level concepts come LATER.
        3. Attaches detailed rationale and revision resources.
        """
        # Collect all concepts requiring study
        concepts_to_revise = set()

        for cid, score in concept_score_map.items():
            if score < STRONG_THRESHOLD:
                concepts_to_revise.add(cid)

        for item in prereq_analysis:
            for wp in item.get("weak_prerequisites", []):
                concepts_to_revise.add(wp["concept_id"])

        if not concepts_to_revise:
            return []

        # Create a subgraph of only concepts requiring revision to get topological order
        # If any prerequisite is missing from the subgraph, we include directed dependencies
        subgraph = self.graph.subgraph(concepts_to_revise).copy()

        # Try topological sort on subgraph; if cycles exist, fallback to in-degree order
        try:
            sorted_cids = list(nx.topological_sort(subgraph))
        except (nx.NetworkXUnfeasible, Exception):
            # Fallback sort by in-degree (nodes with fewer prerequisites first)
            sorted_cids = sorted(list(concepts_to_revise), key=lambda c: self.graph.in_degree(c) if c in self.graph else 0)

        # Build detailed step objects
        path = []
        for cid in sorted_cids:
            node_data = self.graph.nodes.get(cid, {})
            cname = node_data.get("name", f"Concept {cid}")
            score = concept_score_map.get(cid, 0.0)
            status = get_status_from_score(score)

            # Check if this concept is a prerequisite gap for higher concepts
            dependent_weak = []
            for p_item in prereq_analysis:
                for wp in p_item.get("weak_prerequisites", []):
                    if wp["concept_id"] == cid:
                        dependent_weak.append(p_item["concept_name"])

            is_prereq_gap = len(dependent_weak) > 0

            if is_prereq_gap:
                targets_str = ", ".join(set(dependent_weak))
                reason = f"Essential foundational prerequisite for {targets_str}. Rebuilding mastery here directly unlocks higher-level comprehension."
            elif status == "Weak":
                reason = f"Scored {score}% (Weak). Critical topic requiring concept review and fundamental problem solving."
            else:
                reason = f"Scored {score}% (Needs Improvement). Targeted revision and practice will help bridge this concept to Strong."

            path.append({
                "concept_id": cid,
                "concept_name": cname,
                "score": score,
                "status": status,
                "is_prerequisite_gap": is_prereq_gap,
                "reason": reason,
                "target_dependents": dependent_weak,
                "description": node_data.get("description", ""),
                "explanation": node_data.get("explanation", ""),
                "key_points": node_data.get("key_points", ""),
                "code_example": node_data.get("code_example", "")
            })

        return path

    def get_knowledge_map_data(self, student_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Formats node and edge data for Cytoscape.js visualization.
        If student_id is provided, colors nodes based on the student's latest assessment score.
        If student_id is None, colors nodes based on class average scores.
        """
        cursor = self.conn.cursor()

        # Get latest performance per concept for student or class average
        concept_scores = {}
        if student_id:
            cursor.execute("""
                SELECT cp.concept_id, cp.score, cp.status, cp.assessed_at
                FROM ConceptPerformance cp
                JOIN (
                    SELECT concept_id, MAX(performance_id) as max_id
                    FROM ConceptPerformance
                    WHERE student_id = ?
                    GROUP BY concept_id
                ) latest ON cp.performance_id = latest.max_id
            """, (student_id,))
            for row in cursor.fetchall():
                concept_scores[row["concept_id"]] = {
                    "score": row["score"],
                    "status": row["status"]
                }
        else:
            # Class average
            cursor.execute("""
                SELECT concept_id, ROUND(AVG(score), 1) as avg_score, COUNT(DISTINCT student_id) as student_count
                FROM ConceptPerformance
                GROUP BY concept_id
            """)
            for row in cursor.fetchall():
                avg = row["avg_score"]
                concept_scores[row["concept_id"]] = {
                    "score": avg,
                    "status": get_status_from_score(avg),
                    "students_tested": row["student_count"]
                }

        # Build nodes
        nodes = []
        for node_id in self.graph.nodes():
            n = self.graph.nodes[node_id]
            perf = concept_scores.get(node_id, {"score": None, "status": "Unassessed"})

            # Direct prerequisites (predecessors) and dependents (successors)
            prereqs = [self.graph.nodes[p].get("name") for p in self.graph.predecessors(node_id) if p in self.graph]
            dependents = [self.graph.nodes[s].get("name") for s in self.graph.successors(node_id) if s in self.graph]

            nodes.append({
                "data": {
                    "id": str(node_id),
                    "name": n.get("name"),
                    "topic": n.get("topic"),
                    "unit": n.get("unit"),
                    "score": perf["score"],
                    "status": perf["status"],
                    "description": n.get("description"),
                    "explanation": n.get("explanation"),
                    "key_points": n.get("key_points"),
                    "code_example": n.get("code_example"),
                    "prerequisites": prereqs,
                    "dependents": dependents
                }
            })

        # Build edges
        edges = []
        for u, v in self.graph.edges():
            edges.append({
                "data": {
                    "id": f"e_{u}_{v}",
                    "source": str(u),
                    "target": str(v),
                    "label": "prerequisite"
                }
            })

        roots = [str(n) for n in self.graph.nodes() if self.graph.in_degree(n) == 0]

        return {
            "nodes": nodes,
            "edges": edges,
            "roots": roots,
            "total_concepts": len(nodes),
            "thresholds": {
                "strong": STRONG_THRESHOLD,
                "weak": WEAK_THRESHOLD
            }
        }

    def compute_improvement(self, initial_attempt_id: int, followup_attempt_id: int) -> Dict[str, Any]:
        """
        Computes observed improvement between initial and follow-up attempts.
        Matches Section 10 of guidelines.md.
        """
        cursor = self.conn.cursor()

        # Fetch scores for initial attempt
        cursor.execute("SELECT percentage, student_id FROM StudentAttempts WHERE attempt_id = ?", (initial_attempt_id,))
        init_row = cursor.fetchone()
        cursor.execute("SELECT percentage FROM StudentAttempts WHERE attempt_id = ?", (followup_attempt_id,))
        follow_row = cursor.fetchone()

        if not init_row or not follow_row:
            return {"error": "Attempts not found"}

        initial_overall = init_row["percentage"]
        followup_overall = follow_row["percentage"]
        overall_delta = round(followup_overall - initial_overall, 1)

        # Fetch concept performances for both attempts
        cursor.execute("""
            SELECT cp.concept_id, c.concept_name, cp.score, cp.status
            FROM ConceptPerformance cp
            JOIN Concepts c ON cp.concept_id = c.concept_id
            WHERE cp.assessment_id = (SELECT assessment_id FROM StudentAttempts WHERE attempt_id = ?)
              AND cp.student_id = ?
        """, (initial_attempt_id, init_row["student_id"]))
        init_concepts = {row["concept_id"]: dict(row) for row in cursor.fetchall()}

        cursor.execute("""
            SELECT cp.concept_id, c.concept_name, cp.score, cp.status
            FROM ConceptPerformance cp
            JOIN Concepts c ON cp.concept_id = c.concept_id
            WHERE cp.assessment_id = (SELECT assessment_id FROM StudentAttempts WHERE attempt_id = ?)
              AND cp.student_id = ?
        """, (followup_attempt_id, init_row["student_id"]))
        follow_concepts = {row["concept_id"]: dict(row) for row in cursor.fetchall()}

        concept_comparison = []
        for cid, f_data in follow_concepts.items():
            cname = f_data["concept_name"]
            f_score = f_data["score"]
            i_data = init_concepts.get(cid)
            i_score = i_data["score"] if i_data else None

            delta = round(f_score - i_score, 1) if i_score is not None else 0.0

            concept_comparison.append({
                "concept_id": cid,
                "concept_name": cname,
                "initial_score": i_score,
                "initial_status": i_data["status"] if i_data else "N/A",
                "followup_score": f_score,
                "followup_status": f_data["status"],
                "delta": delta,
                "improved": delta > 0
            })

        return {
            "student_id": init_row["student_id"],
            "initial_overall": initial_overall,
            "followup_overall": followup_overall,
            "overall_delta": overall_delta,
            "concepts": concept_comparison
        }

# MASTER PROMPT — COGNIMAP AI

## Project Name

**Cognimap AI — Intelligent Student Knowledge Mapping and Personalized Learning System**

---

## 1. PROJECT VISION

Build a complete, functional, academic-quality web application called **Cognimap AI**.

Cognimap AI is an intelligent student learning analytics and knowledge mapping system designed to help lecturers understand **what concepts students actually understand, where they are weak, and which prerequisite concepts should be revised first**.

The system should not simply calculate marks.

Its main purpose is to:

* Assess students at the **concept level**
* Analyze student performance using AI/ML-based logic
* Identify weak concepts
* Check prerequisite concepts related to those weaknesses
* Generate a visual **Knowledge Map**
* Recommend a personalized learning path
* Conduct a follow-up quiz
* Measure observed improvement
* Provide lecturers with class-level analytics

The system should be explainable, practical, modular, scalable, and suitable for an engineering college mini project.

---

# 2. CORE WORKFLOW

The complete system must follow this workflow:

### Step 1 — Lecturer Login & Setup

The lecturer logs into the system.

The lecturer should be able to create a subject and enter:

* Subject name
* Units
* Topics
* Specific concepts under each topic

Example:

**Subject:** Data Structures

**Unit 1**

* Arrays
* Linked Lists

**Unit 2**

* Stack
* Queue

**Unit 3**

* Recursion
* Trees

**Unit 4**

* Graphs
* BFS
* DFS

The lecturer should be able to establish relationships between concepts where necessary.

Example:

Programming Fundamentals → Recursion → Trees → Graphs → BFS/DFS

---

# 3. QUESTION CREATION

The lecturer creates assessment questions.

Each question should contain:

* Question text
* Question type
* Difficulty level
* Unit
* Topic
* Specific concept being tested
* Correct answer
* Options, if applicable
* Marks

Difficulty levels:

* Easy
* Medium
* Hard

Most importantly, every question should be associated with a **specific concept**.

Example:

Question:
"What is the time complexity of binary search?"

Concept:
Binary Search

Difficulty:
Medium

This concept tagging allows the system to analyze performance at the concept level instead of only calculating total marks.

---

# 4. STUDENT ASSESSMENT

The student logs into Cognimap AI.

The student should be able to:

1. View available subjects
2. Select the assigned assessment
3. Read instructions
4. Answer questions
5. Submit the assessment

The system should record:

* Student answers
* Correct/incorrect answers
* Marks
* Question difficulty
* Concept associated with each question
* Time taken, where applicable
* Assessment attempt

After submission, the system sends the assessment data to the analysis module.

---

# 5. PERFORMANCE ANALYSIS

The system's AI/ML or intelligent analysis component analyzes the student's assessment.

The analysis should calculate:

* Overall score
* Concept-wise score
* Topic-wise performance
* Unit-wise performance
* Difficulty-wise performance
* Strong concepts
* Concepts needing improvement
* Weak concepts

Example:

| Concept      | Score | Status            |
| ------------ | ----: | ----------------- |
| Arrays       |   90% | Strong            |
| Linked Lists |   82% | Strong            |
| Stack        |   76% | Good              |
| Queue        |   70% | Needs Improvement |
| Trees        |   45% | Weak              |
| Graphs       |   32% | Weak              |

Use configurable thresholds rather than hard-coding them.

For example:

* Green → Strong
* Yellow → Needs Improvement
* Red → Weak

The system should clearly explain how each status was determined.

---

# 6. PREREQUISITE CHECK

This is one of the most important features of Cognimap AI.

The system should not assume that a weak concept is an isolated problem.

It should check the prerequisite concepts connected to the weak concept.

Example:

If the student performs poorly in:

**Graphs**

the system checks prerequisite concepts such as:

**Trees → Recursion → Programming Fundamentals**

If the student is also weak in Trees and Recursion, Cognimap AI should identify these as possible prerequisite gaps.

Example:

Graphs = 32%
Trees = 45%
Recursion = 48%

The system can generate:

> "Your performance in Graphs may be affected by weaknesses in prerequisite concepts such as Trees and Recursion."

Do not present this as a psychological or definitive educational diagnosis.

The system should describe it as an **analysis based on assessment performance and predefined concept dependencies**.

---

# 7. KNOWLEDGE MAP GENERATION

The Knowledge Map is the visual centerpiece of Cognimap AI.

After performance and prerequisite analysis, the system generates a visual map of the student's knowledge.

The map should contain:

* Concept nodes
* Concept performance
* Concept status
* Prerequisite relationships
* Dependency arrows
* Strong areas
* Weak areas
* Concepts requiring revision

Example:

Programming Fundamentals
↓
Recursion
↓
Trees
↓
Graphs
↙   ↘
BFS   DFS

The nodes should visually indicate performance.

Example:

🟢 Strong
🟡 Needs Improvement
🔴 Weak

The Knowledge Map should be interactive.

When the student clicks a concept, display:

* Concept name
* Score
* Status
* Related concepts
* Prerequisites
* Recommended action
* Learning resources

The Knowledge Map should make it easy for a student to understand:

**"What do I know?"**

**"What am I weak in?"**

**"Why should I revise this concept first?"**

---

# 8. PERSONALIZED LEARNING PATH

After generating the Knowledge Map, Cognimap AI creates a personalized learning path.

The learning path should be based on:

* Weak concepts
* Prerequisite relationships
* Concept dependencies
* Assessment performance
* Difficulty level

Example:

If Student A has:

Recursion → Weak
Trees → Weak
Graphs → Weak
BFS → Weak
DFS → Weak

The system may recommend:

1. Revise Recursion
2. Revise Trees
3. Learn Graph Basics
4. Practice BFS
5. Practice DFS

However, if Student B has strong Trees but weak Graphs, the system should not unnecessarily recommend Trees.

Instead:

1. Graph Basics
2. BFS
3. DFS

This demonstrates that the learning path is **personalized according to individual performance**.

Each recommendation should explain why it was generated.

---

# 9. LEARNING RECOMMENDATIONS

For each recommended concept, provide useful learning guidance.

Each concept may contain:

* Concept explanation
* Key points
* Recommended study material
* Practice questions
* Examples
* Suggested revision order
* Estimated priority

The system should prioritize concepts based on prerequisite importance and performance.

Avoid creating a generic list of resources unrelated to the student's actual weaknesses.

---

# 10. FOLLOW-UP QUIZ

After the student follows the recommended learning path, they should be able to take a follow-up quiz.

The quiz should focus primarily on:

* Previously weak concepts
* Prerequisite concepts
* Concepts included in the personalized learning path

The system then compares:

### Before

Graphs = 32%

### After

Graphs = 71%

The system should display:

* Previous score
* New score
* Difference
* Percentage improvement
* Concept-wise improvement

Example:

**Graphs**

Before: 32%
After: 71%
Improvement: +39 percentage points

The system should describe this as **observed improvement between assessments**, not claim that the recommendation definitively caused the improvement.

---

# 11. LECTURER ANALYTICS DASHBOARD

The lecturer should have a comprehensive analytics dashboard.

The lecturer should be able to view:

### Class-level information

* Number of students
* Assessment participation
* Average score
* Concept-wise performance
* Unit-wise performance
* Difficulty-wise performance

### Common knowledge gaps

Example:

Graphs → 68% of students need improvement
Recursion → 54%
Trees → 47%

### Individual student analytics

Lecturer can select a student and view:

* Overall score
* Concept-wise performance
* Weak concepts
* Strong concepts
* Knowledge Map
* Prerequisite gaps
* Learning path
* Follow-up quiz performance
* Improvement

### Class Knowledge Map

Provide an aggregated visualization showing which concepts are difficult for the class as a whole.

This helps the lecturer identify concepts that may require additional classroom explanation or practice.

---

# 12. USERS AND ROLES

The system should have two primary roles.

## Lecturer

Lecturer can:

* Register/Login
* Create subjects
* Create units/topics/concepts
* Define concept relationships
* Create questions
* Assign difficulty
* Tag questions to concepts
* Create assessments
* View student results
* View individual analytics
* View class analytics
* View class Knowledge Map

## Student

Student can:

* Register/Login
* View available subjects
* Take assessments
* View results
* View concept-wise performance
* View Knowledge Map
* View prerequisite analysis
* View personalized learning path
* Access recommendations
* Take follow-up quizzes
* Compare progress

---

# 13. AI/ML COMPONENT

Cognimap AI should genuinely contain an intelligent analysis component.

Do not falsely claim that the entire application is powered by advanced AI if it is primarily rule-based.

Use a practical and explainable approach.

The intelligent component may analyze:

* Concept-level performance
* Difficulty-wise performance
* Weak concept identification
* Prerequisite relationships
* Priority of concepts
* Personalized learning recommendations
* Improvement between assessments

A hybrid approach is acceptable:

**Rule-based logic + data analysis + optional ML model**

The system should clearly distinguish:

* Deterministic calculations
* Prerequisite rules
* Recommendation logic
* Any actual ML model

Do not invent fake AI functionality.

---

# 14. DATABASE DESIGN

Design a proper relational database.

Suggested entities:

### Users

* user_id
* name
* email
* password
* role

### Subjects

* subject_id
* subject_name
* lecturer_id

### Units

* unit_id
* subject_id
* unit_name

### Topics

* topic_id
* unit_id
* topic_name

### Concepts

* concept_id
* topic_id
* concept_name
* description

### ConceptDependencies

* dependency_id
* concept_id
* prerequisite_concept_id

### Questions

* question_id
* concept_id
* difficulty
* question_text
* question_type
* marks

### Assessments

* assessment_id
* subject_id
* lecturer_id
* title
* date

### AssessmentQuestions

* assessment_id
* question_id

### StudentAttempts

* attempt_id
* student_id
* assessment_id
* score
* date

### StudentAnswers

* answer_id
* attempt_id
* question_id
* selected_answer
* correctness
* marks

### ConceptPerformance

* performance_id
* student_id
* concept_id
* assessment_id
* score
* status

### LearningPaths

* path_id
* student_id
* concept_id
* priority
* recommendation

### FollowUpAssessments

* followup_id
* student_id
* assessment_id
* score

Design the schema so additional subjects and concepts can easily be added later.

---

# 15. TECHNOLOGY STACK

Use a practical technology stack suitable for a college project.

### Frontend

* HTML
* CSS
* JavaScript
* Bootstrap or another suitable UI framework if required

### Backend

* Java
* Spring Boot
* REST APIs

### Database

* MySQL

### AI/ML

* Python
* Flask/FastAPI if a separate AI service is required
* Python ML/data-analysis libraries where genuinely useful

### Visualization

Use a suitable visualization library such as:

* Chart.js
* D3.js
* React Flow
* Cytoscape.js
* or another appropriate graph visualization library

Choose the simplest reliable option that provides an interactive Knowledge Map.

---

# 16. SYSTEM ARCHITECTURE

Use a modular architecture:

Student/Lecturer
↓
Frontend
↓
Backend / REST API
↓
Business Logic
↓
Database

For AI/ML:

Backend
↓
AI/ML Analysis Service
↓
Performance Analysis
↓
Prerequisite Analysis
↓
Recommendation Engine
↓
Knowledge Map / Learning Path

Keep the AI/ML component modular so it can be improved later without rebuilding the entire application.

---

# 17. UI/UX REQUIREMENTS

The interface should look modern, clean, professional,attractive  and suitable for an engineering college project demonstration.

Create separate dashboards.

### Student Dashboard

Include:

* Welcome section
* Subjects
* Assessments
* Recent results
* Concept performance
* Knowledge Map
* Learning Path
* Follow-up Quiz
* Progress

### Lecturer Dashboard

Include:

* Subjects
* Assessment creation
* Question management
* Student performance
* Class analytics
* Common knowledge gaps
* Class Knowledge Map

Use:

* Cards
* Charts
* Progress bars
* Interactive graphs
* Tables
* Clear status indicators
* Responsive design


---

# 18. SECURITY

Implement basic security practices.

Include:

* Secure authentication
* Password hashing
* Role-based access
* Input validation
* Protected APIs
* Student data privacy
* Lecturer/student authorization

Students should only be able to access their own personal analytics.

Lecturers should only access data for subjects/classes they manage.

---

# 19. INITIAL SUBJECT

For the first working version, use:

**Data Structures**

Suggested concepts:

* Arrays
* Linked Lists
* Stack
* Queue
* Recursion
* Trees
* Binary Search Trees
* Graphs
* BFS
* DFS
* Searching
* Sorting

Create realistic prerequisite relationships.

Do not make every concept dependent on every other concept.

---

# 20. SAMPLE END-TO-END SCENARIO

Demonstrate the system using a realistic student.

Student:

**Student A**

Assessment result:

| Concept      | Score |
| ------------ | ----: |
| Arrays       |   90% |
| Linked Lists |   82% |
| Stack        |   76% |
| Queue        |   70% |
| Recursion    |   48% |
| Trees        |   45% |
| Graphs       |   32% |
| BFS          |   38% |
| DFS          |   35% |

The system identifies:

### Strong

Arrays
Linked Lists
Stack

### Needs Improvement

Queue

### Weak

Recursion
Trees
Graphs
BFS
DFS

The prerequisite analysis identifies:

Recursion → Trees → Graphs → BFS/DFS

The Knowledge Map highlights these weak areas.

The personalized learning path becomes:

**Recursion → Trees → Graph Basics → BFS → DFS**

After preparation, the student takes the follow-up quiz.

Example:

Graphs:

Before: 32%
After: 71%

The system displays the observed improvement.

The lecturer dashboard then aggregates results from all students.

---

# 21. IMPORTANT ACADEMIC REQUIREMENTS

The project must be suitable for:

**B.E. Information Science and Engineering — Mini Project**

The implementation should be:

* Technically realistic
* Explainable
* Demonstrable
* Modular
* Scalable
* Academically defensible

Avoid unsupported claims such as:

* "The AI understands the student's brain."
* "The system guarantees improvement."
* "The system diagnoses learning disabilities."
* "The AI knows exactly why a student failed."

Instead, use academically defensible language such as:

> "The system identifies potential knowledge gaps based on concept-level assessment performance and predefined prerequisite relationships."

---

# 22. DEVELOPMENT APPROACH

Build the application incrementally.

### Phase 1

Project setup and architecture.

### Phase 2

Authentication and role management.

### Phase 3

Lecturer subject/unit/topic/concept setup.

### Phase 4

Question creation and concept tagging.

### Phase 5

Student assessment system.

### Phase 6

Performance calculation.

### Phase 7

Prerequisite analysis.

### Phase 8

Knowledge Map.

### Phase 9

Personalized learning path.

### Phase 10

Follow-up quiz and improvement comparison.

### Phase 11

Lecturer analytics dashboard.

### Phase 12

AI/ML enhancement.

### Phase 13

Testing, security, UI refinement, documentation, and deployment.

Do not attempt to build everything simultaneously.

Each module should be tested before moving to the next module.

---

# 23. TESTING REQUIREMENTS

Test:

* Login
* Registration
* Role permissions
* Subject creation
* Concept creation
* Question creation
* Assessment submission
* Score calculation
* Concept-level analysis
* Prerequisite analysis
* Knowledge Map generation
* Learning path generation
* Follow-up quiz
* Improvement calculation
* Lecturer analytics

Test edge cases such as:

* Student scores zero
* Student scores 100%
* Concept has insufficient questions
* Student skips questions
* No prerequisite exists
* Multiple prerequisites exist
* Student has strong prerequisites but weak target concept
* Student has weak prerequisite and target concepts

---

# 24. DEMONSTRATION FLOW

For the final project demonstration, show the complete journey:

### Lecturer

Login
↓
Create Data Structures subject
↓
Create units/topics/concepts
↓
Define prerequisites
↓
Create questions
↓
Assign difficulty and concepts
↓
Publish assessment

### Student

Login
↓
Take assessment
↓
Submit
↓
View performance
↓
View concept analysis
↓
View prerequisite analysis
↓
View Knowledge Map
↓
View personalized learning path
↓
Prepare
↓
Take follow-up quiz
↓
View improvement

### Lecturer

Open analytics
↓
View individual students
↓
View common class weaknesses
↓
View class Knowledge Map
↓
Analyze overall performance

This complete flow should be functional in the final demonstration.

---

# 25. FUTURE EXPANSION

Design Cognimap AI so that it can later support:

* Operating Systems
* Database Management Systems
* Computer Networks
* Object-Oriented Programming
* Algorithms
* Computer Organization
* Software Engineering
* Multiple departments
* Multiple colleges

Future versions may include:

* More advanced ML models
* Natural-language question generation
* Automatic question difficulty estimation
* Adaptive assessments
* More sophisticated recommendation systems
* Learning-resource integration
* Student progress prediction

These should be treated as future enhancements rather than falsely claiming they already exist.

---

# 26. FINAL SUCCESS CRITERIA

The project is considered successful if a complete user journey works:

**Lecturer creates subject → defines concepts and prerequisites → creates concept-tagged questions → student takes assessment → system analyzes performance → prerequisite gaps are identified → Knowledge Map is generated → personalized learning path is created → student prepares → follow-up quiz is taken → improvement is displayed → lecturer views class-level analytics.**

The final system should clearly demonstrate that Cognimap AI goes beyond simple marks calculation by connecting:

**Assessment → Concept Performance → Prerequisites → Knowledge Map → Personalized Learning → Reassessment → Analytics**

Build the system as a real working application rather than a static prototype.

Prioritize correctness, explainability, usability, modularity, and academic credibility over unnecessary complexity.

# Cognimap AI - Student Knowledge Gap & Confusion Mapping System

Cognimap AI is an intelligent academic diagnostic platform that identifies concept-level learning gaps, maps prerequisite dependencies using Directed Acyclic Graphs (DAG), and synthesizes personalized, topologically sorted remediation paths for students.

---

## 🚀 Key Features

- **Lecturer Management & Curriculum Design**:
  - Create subjects, units, topics, and atomic concepts.
  - Define prerequisite dependencies between concepts.
  - Configure multi-question diagnostic assessments with custom time limits.
  - Access class-wide analytics, question difficulty indexes, and confusion matrix heatmaps.

- **Student Assessment & Dynamic Timer**:
  - Interactive multi-question assessments with client-side countdowns and auto-submission.
  - Real-time response tracking and diagnostic scoring.

- **AI Prerequisite Graph Engine (NetworkX)**:
  - Models academic curricula as a Directed Acyclic Graph (DAG).
  - Pinpoints root-cause prerequisite deficiencies (distinguishing surface errors from foundational misunderstandings).
  - Generates topologically ordered learning pathways with clear pedagogical explanations.

- **Interactive Knowledge Maps**:
  - Visual DAG rendering of student mastery:
    - 🟢 **Strong** ($\ge 75\%$)
    - 🟡 **Needs Improvement** ($50\% - 74\%$)
    - 🔴 **Weak / Knowledge Gap** ($< 50\%$)

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Flask, Flask-CORS, Werkzeug
- **Graph & Analytics Engine**: NetworkX
- **Database**: SQLite with WAL mode & foreign key constraints
- **Frontend**: Vanilla HTML5, Modern CSS Design System, Responsive JavaScript
- **Production Server**: Gunicorn

---

## 📦 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/desaiatharva950-oss/CognimapAi-.git
cd CognimapAi-
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `demo.env` (or `.env.example`) to create your local `.env`:
```bash
cp demo.env .env
```
Update `.env` with a secure random key and faculty registration code:
```env
SECRET_KEY=your-secure-random-secret-key
FACULTY_CODE=FACULTY2026
```

### 5. Initialize Seed Data (Optional)
To populate demo curricula, mock concepts, sample questions, and test accounts:
```bash
python seed_data.py
```
> **Default Test Accounts:**
> - **Lecturer**: `lecturer@cognimap.edu` / `admin123`
> - **Student**: `student@cognimap.edu` / `student123`

### 6. Run the Application

**Development Server:**
```bash
python server.py
```
The server will start at `http://127.0.0.1:5000`.

**Production Server (Gunicorn):**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 server:app
```

---

## 🔒 Security & Data Integrity

- Secret keys and sensitive credentials are kept in `.env` and excluded from version control via `.gitignore`.
- SQLite database binaries (`*.db`) and student records are never tracked in Git.
- Password hashes use SHA-256 / Werkzeug cryptographic hashing.

---

## 📄 License
This project is licensed under the MIT License.

# Enterprise AI Governance Platform (PS-9.1: Graduated Autonomy Engine)

A production-ready solution implementing a **Graduated Autonomy Engine (Human-in-the-Loop & Oversight Controls)**. It evaluates AI-generated actions dynamically, calculates operational risk across multiple dimensions, applies enterprise policies, and determines the appropriate execution level: Automatic execution, User Confirmation, or Governance Review.

---

## 🌟 Key Features

1. **AI Intent Extraction:** Extracts action, subject, scope, and intent confidence from natural language queries using LLM semantic parsing.
2. **Multi-Vector Risk Scorer:** Calculates risks based on:
   - **Reversibility:** Destructive capabilities (e.g., DELETE vs. READ).
   - **Data Scope:** Scale of impact (e.g., records count or transaction amounts).
   - **Regulatory Domain:** Business categories (Healthcare/HIPAA, Finance/PCI-DSS, HR, etc.).
   - **Model Confidence:** Intrinsic confidence score of the LLM extraction.
   - **Historical Trends:** Rejection rate of similar actions.
3. **Adaptive Threshold Calibration (Bonus):** Calibrates risk scores dynamically based on user behavior (lowers risk upon repeated approvals, increases risk on rejections).
4. **Graduated Autonomy Decision Mapping:**
   - **Low Risk (0-30):** Automatic / Autonomous Execution.
   - **Medium Risk (31-60):** Awaits user confirmation (with interactive Confirm/Reject UI).
   - **High Risk (61-100):** Queued into a Human Governance Case for administrator review.
5. **Interactive Dashboard:** Modern React interface for case reviews, policy settings, analytics charts, and audit logs.
6. **Robust Test Coverage:** 19/19 backend tests covering risk engine formulas, policy engines, and DB workflows.

---

## 🏗️ Technical Stack

- **Backend:** FastAPI (Python 3.12), SQLAlchemy ORM, Alembic migrations, Uvicorn server, unittest.
- **Frontend:** React (Vite), Axios, React Router, HTML5 / Vanilla CSS.
- **Database:** PostgreSQL.
- **LLM Provider:** Groq API (Llama 3.3 70B model).

---

## 🚀 Quick Start (Local Run)

### 1. Backend Setup
1. Open PowerShell and go to `/backend`:
   ```bash
   cd backend
   ```
2. Create and activate a python virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables in `backend/.env`:
   ```ini
   DATABASE_URL=postgresql://postgres:governance_password@localhost:5432/governance_db
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=llama-3.3-70b-versatile
   LOG_LEVEL=INFO
   ```
5. Apply Alembic migrations and start server:
   ```bash
   alembic upgrade head
   venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
   ```

### 2. Frontend Setup
1. Go to `/frontend`:
   ```bash
   cd ../frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start local development server:
   ```bash
   npm run dev
   ```

---

## 🐳 Dockerized Run (Local / VPS)

You can containerize and run the entire application stack:

1. Configure `backend/.env` with your `GROQ_API_KEY`.
2. Build and run using Docker Compose from the root directory:
   ```bash
   docker-compose up --build -d
   ```
3. The platform will be live at:
   - **Frontend Dashboard:** `http://localhost` (Port 80)
   - **FastAPI Documentation:** `http://localhost:8000/docs`

---

## 🧪 Testing

To run the unified backend test runner, navigate to `/backend` and execute:
```bash
venv\Scripts\python run_tests.py
```

---

## 🔒 Confidentiality & Deployment Guidelines

To remain compliant with submission constraints:
* **DO NOT** upload this codebase or any output to public GitHub repositories or public web environments.
* Keep your code in a **private** repository when deploying to Render or Vercel. Both platforms support deploying direct from private Git accounts securely.
* For manual deployments on AWS, bundle the application as a private `.zip` or `.tar.gz` archive, transfer it via SCP, and orchestrate with the provided `docker-compose.yml`.

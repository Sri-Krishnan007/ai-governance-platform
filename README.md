# Enterprise AI Governance Platform (PS-9.1: Graduated Autonomy Engine)

A production-ready solution implementing a **Graduated Autonomy Engine (Human-in-the-Loop & Oversight Controls)**. It evaluates AI-generated actions dynamically, calculates operational risk across multiple dimensions, applies enterprise policies, and maps them to appropriate execution levels: Automatic Execution, User Confirmation, or Governance Review.

---

## 🏗️ System Architecture & Workflow

The platform processes incoming AI-generated actions through a structured pipeline:

```mermaid
graph TD
    A[Natural Language Action Request] --> B[LLM Intent Extractor]
    subgraph backend [FastAPI backend/app]
        B --> C{Intent Parsed?}
        C -- Yes --> D[Multi-Vector Risk Scorer]
        C -- No --> E[Request Clarification / Return Parsing Error]
        D --> F[Policy Enforcement Engine]
        F --> G[Adaptive Threshold Calibration]
        G --> H[Graduated Autonomy Decision Mapping]
        H --> I{Decision Level?}
        I -- "Low (0-30)" --> J[AUTOMATIC Execution]
        I -- "Medium (31-60)" --> K[USER_CONFIRMATION Required]
        I -- "High (61-100)" --> L[HUMAN_REVIEW Governance Case]
    end
    subgraph frontend [React frontend/src]
        K --> M[Interactive Confirm/Reject Dialog]
        L --> N[Governance Case Review Dashboard]
    end
    J & M & N --> O[Immutable Audit Logs & In-App Notification System]
```

The system flow proceeds as follows:
1. **LLM parsing:** Natural language requests are parsed by Groq API (Llama 3.3) to extract structured details (action, subject, scope, confidence).
2. **Risk evaluation:** The multi-vector scoring algorithm calculates risk (0-100) based on reversibility, data scope, category, historical averages, and 9 specific safety factors (negation, harmful biasness, confabulation, integrity, abusive, privacy enhanced, dangerous, violent, environmental impacts).
3. **Policy compliance:** Active policy rules are evaluated to check for threshold breaches (e.g., transfers over Rs. 50,000) or domain-specific prohibitions.
4. **Adaptive learning:** Historical patterns dynamically adjust risk thresholds based on past approvals and rejections.
5. **Autonomy mapping:** Low risk triggers autonomous execution, medium risk requests a prompt user confirmation, and high risk routes actions to a governance review queue.

---

## 📁 Codebase Directory Inventory

Below is a detailed map of the key files and folders in the platform codebase:

### Backend Architecture (`/backend`)

| Component | Path | Description |
| :--- | :--- | :--- |
| **Main API Gateway** | [app/main.py](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/backend/app/main.py) | Registers API routers, handles CORS middleware, and executes startup database seeding. |
| **Configuration Settings** | [app/config.py](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/backend/app/config.py) | Defines database connections, JWT secrets, and LLM model configuration using Pydantic Settings. |
| **Database Connection** | [app/database.py](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/backend/app/database.py) | Establishes the SQLAlchemy engine, session maker, and database connectivity helpers. |
| **Data Models & Validation** | [app/models.py](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/backend/app/models.py) / [app/schemas.py](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/backend/app/schemas.py) | Defines database tables (Users, Roles, Actions, GovernanceCases, Policies, AuditLogs, etc.) and Pydantic validators. |
| **Authentication & RBAC** | [app/auth.py](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/backend/app/auth.py) | Implements JWT authorization, password hashing, and role-based access control handlers. |
| **Data Seeding** | [app/seed.py](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/backend/app/seed.py) | Populates the database with default roles, policies, users (`admin`, `reviewer`, `employee`), and mock historical decisions. |
| **Risk Scorer Engine** | [app/services/risk_engine.py](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/backend/app/services/risk_engine.py) | Calculates cumulative risk scores (0-100) using multi-vector risk formulas and safety assessments. |
| **Policy Engine** | [app/services/policy_engine.py](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/backend/app/services/policy_engine.py) | Evaluates active system policies and checks for threshold breaches or domain restrictions. |
| **Intent Extraction (LLM)** | [app/services/llm.py](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/backend/app/services/llm.py) | Interfaces with the Groq API (Llama 3.3) to retrieve structured intent and confidence parameters. |
| **Adaptive Learning Engine** | [app/services/history_engine.py](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/backend/app/services/history_engine.py) | Tracks decision rates to dynamically recalibrate risk scores based on user behavioral history. |
| **Decision Engine** | [app/services/decision_engine.py](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/backend/app/services/decision_engine.py) | Maps risks and policy flags to final autonomy levels: `AUTOMATIC`, `USER_CONFIRMATION`, or `HUMAN_REVIEW`. |
| **Explainability Service** | [app/services/explainability.py](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/backend/app/services/explainability.py) | Explains final autonomy levels and risk assessments in clear, readable English. |
| **Notification Engine** | [app/services/notification_engine.py](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/backend/app/services/notification_engine.py) | Creates audit logs and updates users regarding pending case actions. |
| **Unified Test Suite** | [run_tests.py](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/backend/run_tests.py) | Main test runner executing the complete backend tests inside the `/tests` folder. |

### Frontend Architecture (`/frontend`)

| Component | Path | Description |
| :--- | :--- | :--- |
| **Application Core** | [App.jsx](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/frontend/src/App.jsx) | Declares client-side routes, navigation layouts, and guards. |
| **API Client Settings** | [api.js](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/frontend/src/services/api.js) | Configures Axios, adds JWT authorization to requests, and interceptors to auto-refresh tokens. |
| **Auth Provider** | [AuthContext.jsx](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/frontend/src/context/AuthContext.jsx) | Manages login, registration, and persistent user tokens. |
| **System Dashboard** | [Dashboard.jsx](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/frontend/src/pages/Dashboard.jsx) | Displays system risk trends, safety charts, and governance cases metrics. |
| **Submit Action Page** | [SubmitAction.jsx](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/frontend/src/pages/SubmitAction.jsx) | Allows employees to input natural language statements and see risk evaluations in real time. |
| **Case Review Dashboard** | [GovernanceCases.jsx](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/frontend/src/pages/GovernanceCases.jsx) | Allows reviewers to view pending actions, apply review conditions, and confirm or reject them. |
| **Policy Settings** | [PolicySettings.jsx](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/frontend/src/pages/PolicySettings.jsx) | Allows administrators to create/modify rules, adjust risk weights, and active statuses. |
| **Audit Logs Page** | [AuditLogs.jsx](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/frontend/src/pages/AuditLogs.jsx) | Provides audit compliance tables tracking historical actions and system events. |

---

## ⚙️ Environment Variables Reference

Create a `.env` file in the `/backend` folder to run the application:

| Key | Description | Example Value |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:password@localhost:5432/governance_db` |
| `GROQ_API_KEY` | Your personal Groq API key | `gsk_xxxxxxxxxxxxxxxxxxxxxx` |
| `GROQ_MODEL` | LLM model to parse intentions | `llama-3.3-70b-versatile` |
| `LOG_LEVEL` | Application logging level | `INFO` |
| `SECRET_KEY` | Key to sign authentication JWTs | `a_very_secure_random_string_here` |

For production frontend build configurations:

| Key | Description | Default Value |
| :--- | :--- | :--- |
| `VITE_API_URL` | Target url of the backend FastAPI service | `http://localhost:8000` |

---

## 🚀 Independent Verification & Deployment Guide

To verify platform functionality, you can run or deploy the application using the scripts and configuration files documented below.

### Method 1: Local Deployment Scripts (Local Machine Setup)

The following automated setup scripts are already included in the workspace root directory:

#### A. PowerShell Setup Script (Windows Users: Run `setup-local.ps1` in root)
```powershell
# Automated Local Environment Setup Script
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Initializing AI Governance Platform Local" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check for Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python 3 is required but not installed. Exiting."
    exit 1
}

# Check for Node
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js/npm is required but not installed. Exiting."
    exit 1
}

# 1. Setup Backend virtual environment and dependencies
Write-Host "Installing Backend dependencies..." -ForegroundColor Yellow
cd backend
python -m venv venv
& .\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# 2. Check for backend environment file
if (-not (Test-Path .env)) {
    Write-Host "Creating sample backend .env file..." -ForegroundColor Yellow
    New-Item -ItemType File -Name .env -Value "DATABASE_URL=postgresql://postgres:governance_password@localhost:5432/governance_db`nGROQ_API_KEY=your_key_here`nGROQ_MODEL=llama-3.3-70b-versatile`nLOG_LEVEL=INFO`nSECRET_KEY=change_me_in_prod" | Out-Null
    Write-Host "WARNING: Created .env file. Please edit 'backend/.env' to insert your valid GROQ_API_KEY." -ForegroundColor Red
}

# 3. Setup Frontend dependencies
Write-Host "Installing Frontend dependencies..." -ForegroundColor Yellow
cd ../frontend
npm install

Write-Host "=========================================" -ForegroundColor Green
Write-Host "Setup Completed successfully!" -ForegroundColor Green
Write-Host "Steps to start:" -ForegroundColor Green
Write-Host "1. Configure your GROQ_API_KEY in 'backend/.env'"
Write-Host "2. Start your local PostgreSQL server"
Write-Host "3. In backend folder, run: alembic upgrade head"
Write-Host "4. In backend folder, run: venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"
Write-Host "5. In frontend folder, run: npm run dev"
Write-Host "=========================================" -ForegroundColor Green
```

#### B. Bash Setup Script (Linux / macOS / Git Bash Users: Run `setup-local.sh` in root)
```bash
#!/bin/bash
set -e

echo "========================================="
echo "Initializing AI Governance Platform Local"
echo "========================================="

# Check requirements
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required. Aborting." >&2; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "Node/npm is required. Aborting." >&2; exit 1; }

# Backend Setup
echo "Setting up Backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  echo "Creating default .env..."
  cat <<EOT >> .env
DATABASE_URL=postgresql://postgres:governance_password@localhost:5432/governance_db
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
LOG_LEVEL=INFO
SECRET_KEY=change_me_in_prod
EOT
  echo "WARNING: Created .env file. Please edit backend/.env to insert your GROQ_API_KEY."
fi

# Frontend Setup
echo "Setting up Frontend..."
cd ../frontend
npm install

echo "========================================="
echo "Setup finished. Follow backend/.env configuration prompts above."
echo "========================================="
```

---

### Method 2: Dockerized Run (1-Command Container Orchestration)

To run the entire system inside isolated Docker containers, you can use the pre-configured `docker-compose.yml` file located at the project root:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: ai_gov_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: governance_password
      POSTGRES_DB: governance_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d governance_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: ai_gov_backend
    environment:
      - DATABASE_URL=postgresql://postgres:governance_password@db:5432/governance_db
      - GROQ_API_KEY=${GROQ_API_KEY}
      - GROQ_MODEL=llama-3.3-70b-versatile
      - LOG_LEVEL=INFO
      - SECRET_KEY=supersecret_ai_governance_platform_key_2026_change_me_in_prod
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    command: >
      sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - VITE_API_URL=http://localhost:8000
    container_name: ai_gov_frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  pgdata:
```

#### Running the Container Stack:
1. Export your API key in the shell session:
   - **PowerShell:** `$env:GROQ_API_KEY="gsk_xxxx..."`
   - **Linux/macOS:** `export GROQ_API_KEY="gsk_xxxx..."`
2. Launch the application stack:
   ```bash
   docker-compose up --build -d
   ```
3. Docker Compose will automatically launch the database, run Alembic migrations, seed mock records, start the FastAPI API on `http://localhost:8000`, compile the Vite React app, and serve it via Nginx on `http://localhost`.

---

## 🧪 Running System Tests

Verify the backend calculations, learning logic, and policy validations using the python test runner:

1. Navigate to `/backend`.
2. Activate your virtual environment:
   - **Windows:** `.\venv\Scripts\activate`
   - **macOS/Linux:** `source venv/bin/activate`
3. Run the automated tests:
   ```bash
   python run_tests.py
   ```
4. This executes 19/19 backend tests.

---

## 🔒 Azure Cloud Deployment Guidelines

For deployment to production servers using student subscriptions, comply with the rules below:

### FastAPI Backend (Azure App Service)
Ensure deployment credentials are set up. To push the local backend directory cleanly as the root directory on Azure:
See details in [azdep.txt](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/azdep.txt) or execute:
```bash
git subtree split --prefix=backend -b azure-deploy
git push azure azure-deploy:main --force
git branch -D azure-deploy
```

### React Frontend (Azure Static Web Apps)
The platform compiles and deploys the React frontend from the private repository on commit. Refer to [.github/workflows/azure-static-web-apps-white-ground-0fad09600.yml](file:///c:/Sk%20PC/COLLEGE/Sem%209/Aivar/AI-Governance-Platform/.github/workflows/azure-static-web-apps-white-ground-0fad09600.yml) for CI/CD configurations.

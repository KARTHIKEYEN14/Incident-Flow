# IncidentFlow — Collaborative Incident & Outage War Room

A real-time incident management application built with **FastAPI**, **PostgreSQL**, and **React** (Vite + Tailwind CSS).

## Tech Stack
- **Backend:** FastAPI, SQLAlchemy 2.0 (async), WebSockets, Alembic
- **Frontend:** React 19, Vite, Tailwind CSS, Lucide Icons, React Router
- **Database:** PostgreSQL (with `asyncpg` for async I/O and `psycopg` for migrations)

## Prerequisites
- **Python:** 3.10+ (tested on Python 3.14)
- **Node.js:** v18+ & npm
- **PostgreSQL:** Running locally

## Environment Setup

1. **Database Configuration:**
   Ensure PostgreSQL is running and your `.env` file in the project root contains your database credentials:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:12345@localhost:5432/incident_warroom
   DATABASE_URL_SYNC=postgresql+psycopg://postgres:12345@localhost:5432/incident_warroom
   SECRET_KEY=your-secret-key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ```

2. **Backend Setup:**
   ```powershell
   # Create & activate virtual environment (if not already done)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Install dependencies
   pip install -r backend/requirements.txt

   # Run database migrations
   python migrate.py upgrade

   # (Optional) Seed demo users
   python backend/seed_users.py
   ```

3. **Frontend Setup:**
   ```powershell
   cd frontend-react
   npm install
   cd ..
   ```

---

## Running the Application

You can use the provided `run.ps1` script to start both the backend and frontend simultaneously, or run them manually in separate terminals.

### Method 1: Using the Start Script (Recommended)

Open PowerShell in the project root:
```powershell
.\run.ps1
```
This automatically starts:
- **Backend API:** [http://127.0.0.1:8000](http://127.0.0.1:8000) (Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs))
- **React Frontend:** [http://localhost:5173](http://localhost:5173)

---

### Method 2: Manual Startup

**Terminal 1 — FastAPI Backend:**
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Navigate to backend and start server
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — React Frontend:**
```powershell
cd frontend-react
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Demo Users

You can log in to [http://localhost:5173](http://localhost:5173) using any of the seeded demo accounts (Password for all is `password123`):

| Name | Email | Password |
| :--- | :--- | :--- |
| **Alice Chen** | `alice@warroom.dev` | `password123` |
| **Bob Martinez** | `bob@warroom.dev` | `password123` |
| **Carol Singh** | `carol@warroom.dev` | `password123` |
| **David Kim** | `david@warroom.dev` | `password123` |

# Collaborative Incident & Outage War Room

A real-time incident management application built with FastAPI, PostgreSQL, and Streamlit.

## Prerequisites
- Python 3.14
- PostgreSQL 18 running locally

## Environment Setup
1. Ensure your PostgreSQL server is running.
2. The `.env` file should contain the correct database credentials:
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:12345@localhost:5432/incident_warroom
   DATABASE_URL_SYNC=postgresql+psycopg://postgres:12345@localhost:5432/incident_warroom
   ```

## Running the Application

You can use the provided `run.ps1` script to start both the backend and frontend simultaneously, or run them manually in two separate terminal windows.

### Method 1: Using the start script (Recommended)
Open a PowerShell terminal in the project root and run:
```powershell
.\run.ps1
```

### Method 2: Manual Startup

**Terminal 1 (FastAPI Backend):**
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Set python path and run FastAPI
$env:PYTHONPATH="f:\Collaborative Incident and Outage Reports\incident-war-room\backend"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 (Modern React Frontend - Recommended):**
```powershell
cd frontend-react
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

**Alternative Terminal 2 (Legacy Streamlit Frontend - Fallback):**
```powershell
.\venv\Scripts\Activate.ps1
cd frontend
streamlit run app.py --server.port 8501
```

## Demo Users
You can log in to `http://localhost:8501` using any of the following seeded demo accounts (Password for all is `password123`):
* `alice@warroom.dev`
* `bob@warroom.dev`
* `carol@warroom.dev`
* `david@warroom.dev`

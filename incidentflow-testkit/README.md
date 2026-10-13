# IncidentFlow Testkit: Standalone AI-Powered Testing Toolkit

A standalone, AI-powered testing toolkit for **IncidentFlow** that generates executable pytest test cases grounded in actual application implementation and executes them using an isolated test environment.

The toolkit remains **entirely outside the production application**. It adds no testing UI, no frontend components, and no production API routes to IncidentFlow.

---

## Architecture Overview

```text
incidentflow-testkit/
├── README.md                           # Documentation and usage guide
├── requirements.txt                    # Standalone testing dependencies
├── pyproject.toml                      # Build and pytest configuration
├── .env.example                        # Environment template
├── incidentflow_testkit/
│   ├── __init__.py                     # Package entry point
│   ├── cli.py                          # CLI interface (generate, run, report, etc.)
│   ├── config.py                       # Configuration and database safety guards
│   ├── ai_generator.py                 # Local Ollama client & structured scenario schema
│   ├── feature_discovery.py            # Verified codebase discovery engine
│   ├── test_catalogue.py               # Deduplication, fingerprinting & round-robin selector
│   ├── test_validator.py               # Implementation validator against verified routes
│   ├── test_executor.py                # Safe pytest code builder & isolated test runner
│   └── report.py                       # Terminal execution report formatter
├── tests/                              # Toolkit unit and end-to-end self-tests
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_ai_generator.py
│   ├── test_validator.py
│   ├── test_catalogue.py
│   ├── test_executor.py
│   ├── test_report.py
│   └── test_end_to_end_execution.py
└── generated/                          # Generated test batches, manifests, and reports
    ├── .gitkeep
    └── .gitignore
```

---

## Prerequisites

1. **Python:** 3.10+ (tested and verified on Python 3.14).
2. **Ollama:** Locally installed and running Ollama instance ([https://ollama.com](https://ollama.com)).
3. **Local AI Model:** Instruction-following local model pulled in Ollama (default: `llama3:latest`, or `qwen2.5-coder:latest`, `mistral:latest`, `llama3.2`).

---

## Quickstart Setup Guide (Windows)

### 1. Setup Local Ollama

1. Download and install Ollama from [https://ollama.com/download](https://ollama.com/download).
2. Verify Ollama is running in Windows terminal:
   ```powershell
   ollama --version
   ```
3. Pull a compatible instruction-following model:
   ```powershell
   ollama pull llama3:latest
   ```
4. Verify the model is available locally:
   ```powershell
   ollama list
   ```

### 2. Setup Python Virtual Environment

Open Windows Command Prompt or PowerShell in the `incidentflow-testkit` directory:

```powershell
cd incidentflow-testkit
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

### 3. Configure Environment

Copy the `.env.example` file to `.env`:

```powershell
Copy-Item .env.example .env
```

Key environment variables:
- `OLLAMA_BASE_URL`: URL of the local Ollama daemon (default: `http://localhost:11434`).
- `OLLAMA_MODEL`: Model name to use (default: `llama3:latest`).
- `MAX_TESTS_PER_BATCH`: Maximum tests generated per command (1 to 10, default: `5`).
- `TEST_DATABASE_URL`: Isolated test database (default: in-memory `sqlite+aiosqlite:///:memory:`).

---

## CLI Usage

All commands can be run from the `incidentflow-testkit/` directory:

### 1. Verify AI Model & Discovered Features

Check whether your local Ollama instance is running and has the model:

```powershell
python -m incidentflow_testkit.cli check-ai
```

Inspect verified features discovered from the IncidentFlow codebase:

```powershell
python -m incidentflow_testkit.cli features
```

### 2. Generate New AI Test Cases

Generate up to 5 fresh, grounded test cases:

```powershell
python -m incidentflow_testkit.cli generate
```

To specify a custom limit (between 1 and 10) or custom model:

```powershell
python -m incidentflow_testkit.cli generate --limit 8 --model llama3:latest
```

> **Note:** The `generate` command constructs, validates, and saves test cases to `generated/batch_<timestamp>/`, but **does not execute them**.

### 3. Run the Latest Generated Batch

Execute **only** the latest generated test batch against the isolated test environment:

```powershell
python -m incidentflow_testkit.cli run
```

For verbose pytest output:

```powershell
python -m incidentflow_testkit.cli run -v
```

### 4. View Latest Execution Report

Display the formatted terminal execution report from the latest run:

```powershell
python -m incidentflow_testkit.cli report
```

### 5. Run the Toolkit's Self-Tests

Execute the deterministic test suite verifying the testkit's own functionality:

```powershell
python -m pytest tests -v
```

---

## Safety & Database Protection

- **Production Database Guard:** The testkit strictly validates `TEST_DATABASE_URL`. Any URL targeting the production database name (`incident_warroom`) without an explicit `_test` suffix triggers an immediate `CRITICAL SAFETY VIOLATION` error and halts execution.
- **Zero Raw AI Code Execution:** The AI model is never allowed to execute arbitrary Python, shell commands, or SQL statements. The model only proposes structured scenario inputs and objectives. Trusted Python templates construct the executable pytest functions.
- **Isolated In-Memory SQLite Adapter:** By default, test execution runs against in-memory SQLite with an automated SQLAlchemy compiler adapter that maps PostgreSQL `JSONB` to SQLite `JSON`. This allows zero-friction, lightning-fast testing without modifying production data.
- **Dedicated PostgreSQL Test Database:** If you prefer running against PostgreSQL, set `TEST_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/incident_warroom_test` in `.env`.

---

## How Feature Discovery Works

The discovery engine ([`incidentflow_testkit/feature_discovery.py`](incidentflow_testkit/feature_discovery.py)) inspects the actual IncidentFlow application:
1. **System Health:** `GET /health`
2. **Departments:** `GET /api/v1/auth/departments`, `GET /api/v1/departments`
3. **Authentication:** `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `GET /api/v1/auth/users`
4. **Incident Declaration & Querying:** `POST /api/v1/incidents`, `GET /api/v1/incidents`, `GET /api/v1/incidents/{id}`
5. **Visibility Scoping:** `ORGANIZATION`, `DEPARTMENT`, and `RESTRICTED` visibility rules
6. **Optimistic Concurrency Control (OCC):** `PATCH /api/v1/incidents/{id}/status`, `PATCH /api/v1/incidents/{id}/severity`, `POST /api/v1/incidents/{id}/resolve`
7. **Collaboration:** `POST /api/v1/incidents/{id}/participants`, `GET /api/v1/incidents/{id}/participants`, `POST /api/v1/incidents/{id}/messages`, `GET /api/v1/incidents/{id}/messages`
8. **Audit Trail:** `GET /api/v1/incidents/{id}/events`

Any hypothetical features (such as file uploads, incident deletion, or third-party webhooks) are explicitly excluded from model context.

---

## Deduplication & Round-Robin Cycling

1. **Semantic Fingerprint:** Every scenario is assigned a deterministic SHA-256 fingerprint derived from `category|endpoint|method|expected_status|input_keys`. Superficial renames or rewordings produce the exact same fingerprint.
2. **Round-Robin Selection:** Scenarios are distributed across feature categories so that each batch tests a diverse set of capabilities.
3. **Cycle Rotation:** Generation history is stored in `generated/generation_history.json`. When all unique scenarios have been generated across multiple runs, the catalogue notes the completion of the cycle and advances to the next cycle.

---

## Troubleshooting

- **`Cannot connect to local Ollama daemon`**:
  Ensure Ollama is running. Open Windows terminal and run `ollama serve` or launch Ollama from your Start Menu.
- **`Model '<name>' is not installed in local Ollama`**:
  Run `ollama pull <name>` (e.g. `ollama pull llama3:latest`).
- **`Safety violation: Production database URL detected`**:
  Ensure `TEST_DATABASE_URL` in `.env` uses `sqlite+aiosqlite:///:memory:` or a database name ending with `_test`.

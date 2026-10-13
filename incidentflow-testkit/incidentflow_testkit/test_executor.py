"""Test generator and pytest runner for validated AI test batches."""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from incidentflow_testkit.config import TestkitSettings, get_settings
from incidentflow_testkit.test_catalogue import GenerationBatch


CONFTEST_TEMPLATE = """\"\"\"Isolated Pytest Fixtures for IncidentFlow Generated Batch {batch_id}.\"\"\"

import os
import sys
from pathlib import Path
import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport

# Ensure backend directory is in sys.path
backend_path = Path(r"{backend_dir}")
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

# Register SQLite JSONB adapter for fast, zero-dependency in-memory testing
compiles(JSONB, "sqlite")(lambda type_, compiler, **kw: "JSON")

from app.main import app
from app.db.session import Base, get_db
from app.models.models import Department, User, Incident, IncidentStatus, SeverityLevel, IncidentVisibility, ParticipantRole
from app.core.security import create_access_token
from app.services.auth_service import hash_password

TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", "{test_db_url}")

# Safety check
if "incident_warroom" in TEST_DB_URL.lower() and not "_test" in TEST_DB_URL.lower():
    raise RuntimeError("CRITICAL: Attempted to run tests against production database! Aborting.")

test_engine = create_async_engine(TEST_DB_URL, echo=False)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_test_database():
    \"\"\"Create clean test database tables and seed foundational departments.\"\"\"
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with test_session_factory() as session:
        # Seed foundational departments
        for dept_name in ["Engineering", "Security", "Operations", "Finance"]:
            d = Department(name=dept_name)
            session.add(d)
        await session.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    \"\"\"Yields an isolated async session for direct DB assertions.\"\"\"
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    \"\"\"Async HTTP test client bound directly to the FastAPI ASGI application.\"\"\"
    async def override_get_db():
        async with test_session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_user(db_session: AsyncSession):
    \"\"\"Create a standard test user account.\"\"\"
    from sqlalchemy import select
    res = await db_session.execute(select(Department).where(Department.name == "Engineering"))
    dept = res.scalar_one()

    email = f"tester_{{os.urandom(4).hex()}}@warroom.dev"
    user = User(
        name="Staff Test Engineer",
        email=email,
        password_hash=hash_password("password123"),
        department="Engineering",
        department_id=dept.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(user.id, user.email)
    return {{"user": user, "token": token, "headers": {{"Authorization": f"Bearer {{token}}"}}}}


@pytest_asyncio.fixture
async def seed_incident(db_session: AsyncSession, seed_user: dict):
    \"\"\"Create an incident owned by the test user.\"\"\"
    user = seed_user["user"]
    inc = Incident(
        title="Payment Gateway Timeout Surge",
        service_name="payment-gateway",
        severity=SeverityLevel.SEV2,
        status=IncidentStatus.INVESTIGATING,
        creator_id=user.id,
        commander_id=user.id,
        visibility=IncidentVisibility.ORGANIZATION,
        department="Engineering",
        version=1,
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc
"""


def _build_test_function_code(scn, idx: int) -> str:
    """Generate trusted, executable pytest test code for a single scenario."""
    sc = scn.scenario
    func_name = f"{sc.test_name}_{idx}" if not sc.test_name.endswith(f"_{idx}") else sc.test_name
    func_name = "".join(c if c.isalnum() or c == "_" else "_" for c in func_name)

    endpoint_expr = repr(sc.target_endpoint)
    method = sc.http_method.strip().upper()
    expected_status = sc.expected_status_code
    input_json = json.dumps(sc.input_data)

    lines = [
        f"@pytest.mark.asyncio",
        f"async def {func_name}(client, seed_user, seed_incident):",
        f'    """',
        f'    Scenario ID: {scn.scenario_id}',
        f'    Feature: {sc.feature_name}',
        f'    Category: {sc.category}',
        f'    Objective: {sc.test_objective}',
        f'    Fingerprint: {scn.fingerprint}',
        f'    Source Evidence: {sc.source_evidence}',
        f'    """',
    ]

    if expected_status == 401:
        lines.append("    # Scenario tests unauthorized access with invalid bearer token")
        lines.append("    headers = {'Authorization': 'Bearer invalid_test_token'}")
    elif expected_status == 403 and "without_token" in sc.test_name:
        lines.append("    # Scenario tests missing credentials (HTTPBearer returns 403 by default)")
        lines.append("    headers = {}")
    else:
        lines.append("    headers = seed_user['headers']")

    lines.extend([
        f"    incident_id = str(seed_incident.id)",
        f"    user_id = str(seed_user['user'].id)",
        f"",
        f"    # Resolve dynamic route placeholders",
        f"    endpoint = {endpoint_expr}",
        f"    endpoint = endpoint.replace('{{incident_id}}', incident_id)",
        f"    endpoint = endpoint.replace(':incident_id', incident_id)",
        f"    endpoint = endpoint.replace('{{user_id}}', user_id)",
        f"",
        f"    payload = {input_json}",
        f"    # Populate dynamic values in payload",
        f"    for k, v in payload.items():",
        f"        if isinstance(v, str):",
        f"            payload[k] = v.replace('{{incident_id}}', incident_id).replace('{{user_id}}', user_id)",
        f"",
    ])

    # Build the HTTP request
    if method == "GET":
        lines.append(f"    response = await client.get(endpoint, headers=headers)")
    elif method == "POST":
        lines.append(f"    response = await client.post(endpoint, json=payload, headers=headers)")
    elif method == "PATCH":
        lines.append(f"    response = await client.patch(endpoint, json=payload, headers=headers)")
    elif method == "DELETE":
        lines.append(f"    response = await client.delete(endpoint, headers=headers)")
    else:
        lines.append(f"    response = await client.request('{method}', endpoint, json=payload, headers=headers)")

    lines.append(f"")
    lines.append(f"    # Real assertion against application behavior")
    lines.append(f"    assert response.status_code == {expected_status}, (")
    lines.append(f"        f'Expected HTTP {expected_status} for [{method}] {{endpoint}}, '")
    lines.append(f"        f'got {{response.status_code}}: {{response.text}}'")
    lines.append(f"    )")
    lines.append(f"")

    # Additional assertion checks based on status code
    if expected_status in (200, 201):
        lines.append(f"    body = response.json()")
        lines.append(f"    assert body is not None, 'Response body should not be empty'")
    elif expected_status in (400, 401, 403, 404, 409, 422):
        lines.append(f"    body = response.json()")
        lines.append(f"    assert 'detail' in body, 'Error response should contain detail field'")

    return "\n".join(lines)


def generate_pytest_files(batch: GenerationBatch, settings: TestkitSettings | None = None) -> Path:
    """
    Write generated pytest test files and conftest into a dedicated batch directory.
    Updates latest_batch.json manifest.
    """
    cfg = settings or get_settings()
    batch_dir = cfg.generated_dir / batch.batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write conftest.py
    conftest_content = CONFTEST_TEMPLATE.format(
        batch_id=batch.batch_id,
        backend_dir=str(cfg.backend_dir).replace("\\", "\\\\"),
        test_db_url=cfg.test_database_url,
    )
    with open(batch_dir / "conftest.py", "w", encoding="utf-8") as f:
        f.write(conftest_content)

    # 2. Write test_generated.py
    test_lines = [
        f'"""Generated executable pytest tests for batch {batch.batch_id}."""',
        f"",
        f"import pytest",
        f"",
    ]
    for idx, scn in enumerate(batch.scenarios, 1):
        test_lines.append(_build_test_function_code(scn, idx))
        test_lines.append("")

    test_file_path = batch_dir / f"test_{batch.batch_id}.py"
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(test_lines))

    # 3. Update latest_batch.json manifest
    manifest_data = {
        "batch_id": batch.batch_id,
        "batch_dir": str(batch_dir),
        "test_file": str(test_file_path),
        "model_used": batch.model_used,
        "created_at": batch.created_at.isoformat(),
        "total_tests": len(batch.scenarios),
        "scenarios": [
            {
                "scenario_id": s.scenario_id,
                "test_name": s.scenario.test_name,
                "feature": s.scenario.feature_name,
                "category": s.scenario.category,
                "objective": s.scenario.test_objective,
                "endpoint": s.scenario.target_endpoint,
                "method": s.scenario.http_method,
                "expected_status": s.scenario.expected_status_code,
                "fingerprint": s.fingerprint,
            }
            for s in batch.scenarios
        ],
    }
    with open(cfg.latest_batch_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    return test_file_path


def run_latest_batch(
    verbose: bool = False,
    settings: TestkitSettings | None = None,
) -> tuple[dict[str, Any], int]:
    """
    Execute ONLY the latest generated batch via pytest.
    Returns (report_dict, exit_code).
    """
    cfg = settings or get_settings()

    if not cfg.latest_batch_file.exists():
        raise FileNotFoundError(
            "No generated batch manifest found. Please run 'generate' first to create test cases."
        )

    with open(cfg.latest_batch_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    test_file = Path(manifest["test_file"])
    if not test_file.exists():
        raise FileNotFoundError(f"Latest batch test file not found at: {test_file}")

    # Build pytest command targeting ONLY this single generated test file
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_file),
        "-v" if verbose else "-q",
        "--tb=short",
        "-o",
        "asyncio_mode=auto",
    ]

    start_time = time.time()
    env = os.environ.copy()
    env["TEST_DATABASE_URL"] = cfg.test_database_url
    env["PYTHONPATH"] = str(cfg.backend_dir) + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        cmd,
        cwd=str(test_file.parent),
        capture_output=True,
        text=True,
        env=env,
    )
    duration = time.time() - start_time

    # Parse pytest output
    stdout = result.stdout
    stderr = result.stderr
    exit_code = result.returncode

    # Build execution report
    passed_count = stdout.count(" PASSED")
    failed_count = stdout.count(" FAILED")
    error_count = stdout.count(" ERROR")

    # If count not parsed from markers, deduce from exit_code
    if passed_count == 0 and failed_count == 0 and error_count == 0:
        if exit_code == 0:
            passed_count = manifest.get("total_tests", 0)
        else:
            failed_count = manifest.get("total_tests", 0)

    report_data = {
        "batch_id": manifest["batch_id"],
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "model_used": manifest.get("model_used", "unknown"),
        "total_tests": manifest.get("total_tests", 0),
        "passed": passed_count,
        "failed": failed_count,
        "errors": error_count,
        "duration_seconds": round(duration, 3),
        "exit_code": exit_code,
        "status": "PASSED" if exit_code == 0 else "FAILED",
        "scenarios": manifest.get("scenarios", []),
        "stdout": stdout,
        "stderr": stderr,
    }

    # Persist report
    with open(cfg.latest_report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    return report_data, exit_code

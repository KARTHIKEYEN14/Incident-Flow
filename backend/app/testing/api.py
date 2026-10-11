"""FastAPI Router for the Automated Testing Module."""

import uuid
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.db.session import get_db
from app.services.auth_service import get_user_by_id
from app.testing.feature_discovery import discover_features
from app.testing.models import (
    FeatureSnapshot,
    RunStatus,
    TestCaseRecord,
    TestCaseResultRecord,
    TestRunRecord,
)
from app.testing.schemas import (
    FeatureInventory,
    RunTestsRequest,
    TestCaseDefinition,
    TestCaseResponse,
    TestRunDetailResponse,
    TestRunSummary,
)
from app.testing.test_case_generator import (
    GENERATOR_VERSION,
    compute_test_fingerprint,
    generate_and_validate_suite,
    generate_incidentflow_tests,
    select_round_robin_batch,
)
from app.testing.test_executor import executor_instance
from app.testing.test_reporter import generate_test_run_report

router = APIRouter(prefix="/testing", tags=["Automated Testing"])


# ---------------------------------------------------------------------------
# Feature Discovery
# ---------------------------------------------------------------------------

@router.get("/features", response_model=FeatureInventory)
async def get_discovered_features():
    """Return the verified feature inventory extracted from the codebase."""
    return discover_features()


# ---------------------------------------------------------------------------
# Test Case Generation & Round-Robin Batching
# ---------------------------------------------------------------------------

async def get_latest_batch_snapshot(db: AsyncSession) -> Optional[dict]:
    """Retrieve the latest batch generation metadata and test IDs from FeatureSnapshot."""
    stmt = (
        select(FeatureSnapshot)
        .order_by(desc(FeatureSnapshot.discovered_at))
        .limit(1)
    )
    res = await db.execute(stmt)
    snapshot = res.scalar_one_or_none()
    if snapshot and isinstance(snapshot.features, dict) and snapshot.features.get("type") == "batch_generation":
        return snapshot.features
    return None


@router.post("/generate", response_model=dict)
async def generate_test_cases(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Generate and validate a fresh batch of 5 distinct test cases using round-robin selection.
    Persists batch state, selection history, and test definitions.
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    inventory = discover_features()
    all_approved, validation_errors = generate_and_validate_suite()

    # Query latest batch state
    last_snapshot_data = await get_latest_batch_snapshot(db)
    if last_snapshot_data:
        history_fps = last_snapshot_data.get("history_fingerprints", [])
        last_batch_num = last_snapshot_data.get("batch_number", 0)
        last_round_num = last_snapshot_data.get("round_number", 1)
    else:
        history_fps = []
        last_batch_num = 0
        last_round_num = 1

    (
        batch_tests,
        batch_num,
        round_num,
        cycle_restarted,
        updated_history,
        message,
    ) = select_round_robin_batch(
        catalogue=all_approved,
        history_fingerprints=history_fps,
        batch_size=5,
        last_batch_number=last_batch_num,
        last_round_number=last_round_num,
    )

    # Save feature snapshot with batch metadata
    snapshot = FeatureSnapshot(
        generator_version=GENERATOR_VERSION,
        feature_count=len(batch_tests),
        features={
            "type": "batch_generation",
            "batch_number": batch_num,
            "round_number": round_num,
            "cycle_restarted": cycle_restarted,
            "batch_test_ids": [t.id for t in batch_tests],
            "batch_fingerprints": [compute_test_fingerprint(t) for t in batch_tests],
            "history_fingerprints": updated_history,
            "message": message,
        },
    )
    db.add(snapshot)

    # Upsert all approved test definitions to DB for foreign keys & integrity
    for tc in all_approved:
        existing = await db.get(TestCaseRecord, tc.id)
        if existing:
            existing.test_key = tc.test_key
            existing.feature_name = tc.feature_name
            existing.category = tc.category
            existing.title = tc.title
            existing.description = tc.description
            existing.source_evidence = tc.source_evidence
            existing.preconditions = tc.preconditions
            existing.test_steps = tc.test_steps
            existing.input_data = tc.input_data
            existing.expected_outcome = tc.expected_outcome
            existing.generator_version = tc.generator_version
        else:
            rec = TestCaseRecord(
                id=tc.id,
                test_key=tc.test_key,
                feature_name=tc.feature_name,
                category=tc.category,
                title=tc.title,
                description=tc.description,
                source_evidence=tc.source_evidence,
                preconditions=tc.preconditions,
                test_steps=tc.test_steps,
                input_data=tc.input_data,
                expected_outcome=tc.expected_outcome,
                generator_version=tc.generator_version,
            )
            db.add(rec)

    await db.commit()

    return {
        "status": "success",
        "generator_version": GENERATOR_VERSION,
        "engine": inventory.engine,
        "batch_number": batch_num,
        "round_number": round_num,
        "cycle_restarted": cycle_restarted,
        "total_catalogue_size": len(all_approved),
        "generated_tests_count": len(batch_tests),
        "batch_tests": [TestCaseResponse.model_validate(t) for t in batch_tests],
        "validation_errors_count": len(validation_errors),
        "message": message,
    }


@router.get("/batch", response_model=dict)
async def get_current_batch(
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the current active batch metadata and test cases."""
    all_approved, _ = generate_and_validate_suite()
    test_map = {t.id: t for t in all_approved}
    last_data = await get_latest_batch_snapshot(db)
    if last_data and last_data.get("batch_test_ids"):
        batch_ids = last_data["batch_test_ids"]
        tests = [test_map[tid] for tid in batch_ids if tid in test_map]
        batch_num = last_data.get("batch_number", 1)
        round_num = last_data.get("round_number", 1)
        cycle_restarted = last_data.get("cycle_restarted", False)
        message = last_data.get("message", f"Current Batch {batch_num}")
    else:
        # Default first batch of 5
        tests, batch_num, round_num, cycle_restarted, _, message = select_round_robin_batch(
            all_approved, [], batch_size=5, last_batch_number=0, last_round_number=1
        )

    return {
        "status": "success",
        "batch_number": batch_num,
        "round_number": round_num,
        "cycle_restarted": cycle_restarted,
        "total_catalogue_size": len(all_approved),
        "generated_tests_count": len(tests),
        "batch_tests": [TestCaseResponse.model_validate(t) for t in tests],
        "message": message,
    }


# ---------------------------------------------------------------------------
# Test Cases Listing
# ---------------------------------------------------------------------------

@router.get("/cases", response_model=list[TestCaseResponse])
async def list_test_cases(
    feature: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    all: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """List test cases. Defaults to the current active batch of 5 test cases."""
    all_approved, _ = generate_and_validate_suite()
    test_map = {t.id: t for t in all_approved}

    if all:
        tests = all_approved
    else:
        last_data = await get_latest_batch_snapshot(db)
        if last_data and last_data.get("batch_test_ids"):
            batch_ids = last_data["batch_test_ids"]
            tests = [test_map[tid] for tid in batch_ids if tid in test_map]
        else:
            # Default to first batch of 5
            tests, _, _, _, _, _ = select_round_robin_batch(
                all_approved, [], batch_size=5, last_batch_number=0, last_round_number=1
            )

    if feature:
        tests = [t for t in tests if t.feature_name == feature]
    if category:
        tests = [t for t in tests if t.category == category]

    return [TestCaseResponse.model_validate(t) for t in tests]


# ---------------------------------------------------------------------------
# Run Execution
# ---------------------------------------------------------------------------

@router.post("/run", response_model=TestRunDetailResponse)
async def run_tests(
    req: Optional[RunTestsRequest] = None,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Execute test cases against the isolated PostgreSQL test database.
    Defaults to executing only the current generated batch of 5 test cases.
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    all_tests, _ = generate_and_validate_suite()
    test_map = {t.id: t for t in all_tests}

    if req and req.test_case_ids:
        target_ids = set(req.test_case_ids)
        tests_to_run = [t for t in all_tests if t.id in target_ids]
    elif req and req.feature_filter:
        tests_to_run = [t for t in all_tests if t.feature_name == req.feature_filter]
    else:
        # Default to only the current active batch of 5 test cases
        last_data = await get_latest_batch_snapshot(db)
        if last_data and last_data.get("batch_test_ids"):
            batch_ids = last_data["batch_test_ids"]
            tests_to_run = [test_map[tid] for tid in batch_ids if tid in test_map]
        else:
            tests_to_run, _, _, _, _, _ = select_round_robin_batch(
                all_tests, [], batch_size=5, last_batch_number=0, last_round_number=1
            )

    if not tests_to_run:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No eligible test cases selected for execution.",
        )

    # Ensure test case records exist in DB for FK relationships
    for tc in tests_to_run:
        existing = await db.get(TestCaseRecord, tc.id)
        if not existing:
            rec = TestCaseRecord(
                id=tc.id,
                test_key=tc.test_key,
                feature_name=tc.feature_name,
                category=tc.category,
                title=tc.title,
                description=tc.description,
                source_evidence=tc.source_evidence,
                preconditions=tc.preconditions,
                test_steps=tc.test_steps,
                input_data=tc.input_data,
                expected_outcome=tc.expected_outcome,
                generator_version=tc.generator_version,
            )
            db.add(rec)
    await db.commit()

    # Create TestRunRecord
    run_record = TestRunRecord(
        status=RunStatus.PENDING.value,
        generator_version=GENERATOR_VERSION,
        triggered_by=user.email,
        total_tests=len(tests_to_run),
    )
    db.add(run_record)
    await db.commit()
    await db.refresh(run_record)

    # Execute tests in isolated test environment
    await executor_instance.execute_run(run_record.id, tests_to_run, db)

    # Generate and return full report
    return await generate_test_run_report(run_record.id, db)


# ---------------------------------------------------------------------------
# Test Run History & Details
# ---------------------------------------------------------------------------

@router.get("/runs", response_model=list[TestRunSummary])
async def list_test_runs(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Retrieve historical test runs with timestamps and aggregate metrics."""
    stmt = (
        select(TestRunRecord)
        .order_by(desc(TestRunRecord.created_at))
        .limit(limit)
    )
    res = await db.execute(stmt)
    records = list(res.scalars().all())

    summaries: list[TestRunSummary] = []
    for r in records:
        pass_pct = (r.passed_tests / r.total_tests * 100) if r.total_tests > 0 else 0.0
        summaries.append(
            TestRunSummary(
                id=r.id,
                created_at=r.created_at,
                started_at=r.started_at,
                completed_at=r.completed_at,
                status=r.status,
                generator_version=r.generator_version,
                triggered_by=r.triggered_by,
                total_tests=r.total_tests,
                passed_tests=r.passed_tests,
                failed_tests=r.failed_tests,
                blocked_tests=r.blocked_tests,
                skipped_tests=r.skipped_tests,
                duration_ms=r.duration_ms,
                pass_percentage=round(pass_pct, 1),
                summary_notes=r.summary_notes,
            )
        )
    return summaries


@router.get("/runs/{run_id}", response_model=TestRunDetailResponse)
async def get_test_run_details(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Retrieve detailed execution report, assertions, and timings for a specific test run."""
    try:
        return await generate_test_run_report(run_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/runs/{run_id}/cancel", response_model=dict)
async def cancel_test_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Cancel an active test run."""
    run_record = await db.get(TestRunRecord, run_id)
    if not run_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test run not found.")

    if run_record.status == RunStatus.RUNNING.value:
        run_record.status = RunStatus.CANCELLED.value
        await db.commit()
        return {"status": "cancelled", "run_id": str(run_id)}

    return {"status": run_record.status, "message": "Test run is not currently running."}

"""Reporting and metrics aggregation engine for IncidentFlow test runs."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.testing.models import TestCaseResultRecord, TestRunRecord
from app.testing.schemas import (
    TestCaseResultResponse,
    TestRunDetailResponse,
    TestRunSummary,
)


def build_staff_summary_text(run: TestRunRecord, feature_groups: dict[str, list[TestCaseResultRecord]]) -> str:
    """Generate a concise, human-readable summary for college staff."""
    if run.total_tests == 0:
        return "No tests executed."

    pass_pct = (run.passed_tests / run.total_tests * 100) if run.total_tests > 0 else 0.0

    highlights: list[str] = []
    for feat, results in feature_groups.items():
        feat_passed = sum(1 for r in results if r.status == "PASSED")
        feat_failed = sum(1 for r in results if r.status == "FAILED")
        if feat_failed > 0:
            first_fail = next(r for r in results if r.status == "FAILED")
            highlights.append(f"{feat}: {feat_passed} passed, {feat_failed} failed ({first_fail.title} encountered an error).")
        else:
            highlights.append(f"{feat}: {feat_passed} passed.")

    summary = (
        f"Evaluation Complete ({pass_pct:.1f}% Pass Rate). "
        f"Total: {run.total_tests} | Passed: {run.passed_tests} | "
        f"Failed: {run.failed_tests} | Blocked: {run.blocked_tests} | Skipped: {run.skipped_tests}. "
        f"Execution Time: {run.duration_ms / 1000.0:.2f}s.\n"
        + " | ".join(highlights[:5])
    )
    return summary


async def generate_test_run_report(run_id: UUID, db: AsyncSession) -> TestRunDetailResponse:
    """Generate a detailed report for a specific test run."""
    run_record = await db.get(TestRunRecord, run_id)
    if not run_record:
        raise ValueError(f"Test run {run_id} not found.")

    res_stmt = (
        select(TestCaseResultRecord)
        .where(TestCaseResultRecord.run_id == run_id)
        .order_by(TestCaseResultRecord.executed_at)
    )
    result = await db.execute(res_stmt)
    records = list(result.scalars().all())

    # Group by feature
    results_by_feature: dict[str, list[TestCaseResultResponse]] = {}
    feature_counts: dict[str, dict[str, int]] = {}

    pydantic_results: list[TestCaseResultResponse] = []
    for r in records:
        resp = TestCaseResultResponse.model_validate(r)
        pydantic_results.append(resp)

        feat = r.feature_name
        if feat not in results_by_feature:
            results_by_feature[feat] = []
            feature_counts[feat] = {"total": 0, "passed": 0, "failed": 0, "blocked": 0, "skipped": 0}

        results_by_feature[feat].append(resp)
        feature_counts[feat]["total"] += 1
        st = r.status.lower()
        if st in feature_counts[feat]:
            feature_counts[feat][st] += 1

    feature_summaries: list[dict[str, Any]] = []
    for feat, counts in feature_counts.items():
        total = counts["total"]
        passed = counts["passed"]
        rate = (passed / total * 100) if total > 0 else 0.0
        feature_summaries.append({
            "feature_name": feat,
            "total": total,
            "passed": passed,
            "failed": counts["failed"],
            "blocked": counts["blocked"],
            "skipped": counts["skipped"],
            "pass_rate": round(rate, 1),
            "healthy": counts["failed"] == 0 and counts["blocked"] == 0,
        })

    # Sort feature summaries by fail count descending then name
    feature_summaries.sort(key=lambda f: (-f["failed"], f["feature_name"]))

    pass_percentage = (
        (run_record.passed_tests / run_record.total_tests * 100)
        if run_record.total_tests > 0
        else 0.0
    )

    run_summary = TestRunSummary(
        id=run_record.id,
        created_at=run_record.created_at,
        started_at=run_record.started_at,
        completed_at=run_record.completed_at,
        status=run_record.status,
        generator_version=run_record.generator_version,
        triggered_by=run_record.triggered_by,
        total_tests=run_record.total_tests,
        passed_tests=run_record.passed_tests,
        failed_tests=run_record.failed_tests,
        blocked_tests=run_record.blocked_tests,
        skipped_tests=run_record.skipped_tests,
        duration_ms=run_record.duration_ms,
        pass_percentage=round(pass_percentage, 1),
        summary_notes=run_record.summary_notes,
    )

    return TestRunDetailResponse(
        run=run_summary,
        results=pydantic_results,
        results_by_feature=results_by_feature,
        feature_summaries=feature_summaries,
    )

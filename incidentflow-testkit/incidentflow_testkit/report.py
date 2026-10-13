"""Report formatter for displaying execution results in terminal."""

import json
from pathlib import Path
from typing import Any

from incidentflow_testkit.config import TestkitSettings, get_settings


def load_latest_report(settings: TestkitSettings | None = None) -> dict[str, Any] | None:
    """Load latest report from disk."""
    cfg = settings or get_settings()
    if not cfg.latest_report_file.exists():
        return None
    try:
        with open(cfg.latest_report_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def format_terminal_report(report: dict[str, Any]) -> str:
    """Format execution report into a clean, readable terminal report."""
    batch_id = report.get("batch_id", "Unknown")
    executed_at = report.get("executed_at", "Unknown")
    model_used = report.get("model_used", "Unknown")
    total = report.get("total_tests", 0)
    passed = report.get("passed", 0)
    failed = report.get("failed", 0)
    errors = report.get("errors", 0)
    duration = report.get("duration_seconds", 0.0)
    status = report.get("status", "UNKNOWN")
    exit_code = report.get("exit_code", 1)

    lines = [
        "=" * 72,
        f" INCIDENTFLOW TESTKIT - EXECUTION REPORT",
        "=" * 72,
        f"Batch ID:        {batch_id}",
        f"Executed At:     {executed_at}",
        f"AI Model:        {model_used}",
        f"Total Tests:     {total}",
        f"Passed:          {passed}",
        f"Failed:          {failed}",
        f"Errors:          {errors}",
        f"Duration:        {duration:.2f}s",
        f"Overall Status:  {status} (exit code: {exit_code})",
        "-" * 72,
        "EXECUTED SCENARIOS:",
        "-" * 72,
    ]

    scenarios = report.get("scenarios", [])
    if scenarios:
        for s in scenarios:
            lines.append(
                f"[{s.get('scenario_id', 'SCN')}] {s.get('category', 'Category')}: {s.get('test_name', '')}"
            )
            lines.append(f"  Target:     [{s.get('method', 'GET')}] {s.get('endpoint', '')}")
            lines.append(f"  Objective:  {s.get('objective', '')}")
            lines.append(f"  Expected:   HTTP {s.get('expected_status', '')}")
            lines.append(f"  Fingerprint: {s.get('fingerprint', '')}")
            lines.append("")
    else:
        lines.append("  No individual scenario metadata recorded.")
        lines.append("")

    if status != "PASSED" and (report.get("stdout") or report.get("stderr")):
        lines.append("-" * 72)
        lines.append("PYTEST DIAGNOSTIC OUTPUT:")
        lines.append("-" * 72)
        if report.get("stderr"):
            lines.append("STDERR:")
            lines.append(report["stderr"].strip())
        if report.get("stdout"):
            lines.append("STDOUT:")
            lines.append(report["stdout"].strip())
        lines.append("")

    lines.append("=" * 72)
    return "\n".join(lines)


def display_latest_report(settings: TestkitSettings | None = None) -> int:
    """Print the latest execution report to stdout. Returns exit code."""
    cfg = settings or get_settings()
    report = load_latest_report(cfg)
    if not report:
        print("\n[!] No test execution report found.")
        print("Please run tests first using: python -m incidentflow_testkit.cli run\n")
        return 1

    formatted = format_terminal_report(report)
    print(formatted)
    return report.get("exit_code", 0)

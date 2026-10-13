"""Unit tests for report formatting."""

from incidentflow_testkit.report import format_terminal_report, load_latest_report


def test_format_terminal_report_output():
    report_data = {
        "batch_id": "batch_20261013_120000_abc123",
        "executed_at": "2026-10-13T06:55:00Z",
        "model_used": "llama3:latest",
        "total_tests": 2,
        "passed": 2,
        "failed": 0,
        "errors": 0,
        "duration_seconds": 0.42,
        "status": "PASSED",
        "exit_code": 0,
        "scenarios": [
            {
                "scenario_id": "SCN-001",
                "test_name": "test_health_probe",
                "category": "SystemHealth",
                "endpoint": "/health",
                "method": "GET",
                "objective": "Verify health probe",
                "expected_status": 200,
                "fingerprint": "a1b2c3d4e5f60718",
            }
        ],
    }

    formatted = format_terminal_report(report_data)
    assert "INCIDENTFLOW TESTKIT - EXECUTION REPORT" in formatted
    assert "batch_20261013_120000_abc123" in formatted
    assert "llama3:latest" in formatted
    assert "PASSED" in formatted
    assert "SCN-001" in formatted


def test_load_latest_report_missing_file(test_settings):
    report = load_latest_report(test_settings)
    assert report is None

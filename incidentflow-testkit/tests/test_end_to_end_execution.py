"""End-to-end execution test verifying generated pytest files run against real backend."""

import pytest
from incidentflow_testkit.test_catalogue import TestCatalogue
from incidentflow_testkit.test_executor import generate_pytest_files, run_latest_batch


def test_real_backend_end_to_end_batch_execution(test_settings, sample_scenarios):
    """
    Verify that generated test files execute real assertions against
    the actual IncidentFlow FastAPI application using the isolated test database.
    """
    catalogue = TestCatalogue(test_settings)
    # Select sample scenarios covering real endpoints
    batch, _ = catalogue.select_batch(sample_scenarios[:3], model_name="llama3:latest", limit=3)

    test_file_path = generate_pytest_files(batch, test_settings)
    assert test_file_path.exists()

    # Execute the generated batch with the real pytest runner
    report, exit_code = run_latest_batch(verbose=True, settings=test_settings)

    assert exit_code == 0, f"Generated test run failed! Output:\n{report.get('stdout')}\n{report.get('stderr')}"
    assert report["status"] == "PASSED"
    assert report["passed"] == 3
    assert report["failed"] == 0
    assert report["total_tests"] == 3

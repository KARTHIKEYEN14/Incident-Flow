"""Unit tests for test executor and pytest runner invocation."""

import json
from unittest.mock import patch, MagicMock
import pytest
from incidentflow_testkit.test_catalogue import TestCatalogue
from incidentflow_testkit.test_executor import generate_pytest_files, run_latest_batch


def test_generate_pytest_files_and_manifest(test_settings, sample_scenarios):
    """Verify test files and latest_batch.json are properly generated."""
    catalogue = TestCatalogue(test_settings)
    batch, _ = catalogue.select_batch(sample_scenarios[:2], model_name="llama3:latest", limit=2)

    test_file_path = generate_pytest_files(batch, test_settings)
    assert test_file_path.exists()
    assert test_settings.latest_batch_file.exists()

    with open(test_settings.latest_batch_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["batch_id"] == batch.batch_id
    assert manifest["total_tests"] == 2
    assert len(manifest["scenarios"]) == 2


def test_run_latest_batch_success_and_report(test_settings, sample_scenarios):
    """Verify run_latest_batch executes subprocess and produces report."""
    catalogue = TestCatalogue(test_settings)
    batch, _ = catalogue.select_batch(sample_scenarios[:2], model_name="llama3:latest", limit=2)
    generate_pytest_files(batch, test_settings)

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "test_case_1 PASSED\ntest_case_2 PASSED\n"
    mock_proc.stderr = ""

    with patch("subprocess.run", return_value=mock_proc):
        report, exit_code = run_latest_batch(verbose=False, settings=test_settings)

    assert exit_code == 0
    assert report["status"] == "PASSED"
    assert report["passed"] == 2
    assert test_settings.latest_report_file.exists()


def test_run_latest_batch_failure_exit_code(test_settings, sample_scenarios):
    """Verify nonzero exit code on test failure."""
    catalogue = TestCatalogue(test_settings)
    batch, _ = catalogue.select_batch(sample_scenarios[:1], model_name="llama3:latest", limit=1)
    generate_pytest_files(batch, test_settings)

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stdout = "test_case_1 FAILED\nAssertionError: Expected 200 got 500"
    mock_proc.stderr = ""

    with patch("subprocess.run", return_value=mock_proc):
        report, exit_code = run_latest_batch(verbose=False, settings=test_settings)

    assert exit_code == 1
    assert report["status"] == "FAILED"
    assert report["failed"] == 1

"""Unit tests for test scenario validator."""

import pytest
from incidentflow_testkit.ai_generator import ProposedTestScenario
from incidentflow_testkit.test_validator import TestScenarioValidator
from incidentflow_testkit.feature_discovery import discover_incidentflow_features


def test_validator_accepts_grounded_scenario(sample_scenarios):
    validator = TestScenarioValidator(discover_incidentflow_features())
    for sc in sample_scenarios:
        is_valid, reason = validator.validate_scenario(sc)
        assert is_valid is True, f"Expected scenario to be valid, rejected: {reason}"


def test_validator_rejects_unimplemented_endpoint():
    validator = TestScenarioValidator(discover_incidentflow_features())

    # Fabricated billing endpoint
    fake_scenario = ProposedTestScenario(
        feature_name="Billing",
        test_name="test_checkout",
        test_objective="Test payment",
        target_endpoint="/api/v1/billing/checkout",
        http_method="POST",
        category="Authentication",
        test_steps=["POST checkout"],
        input_data={"amount": 100},
        expected_status_code=200,
        expected_behavior="Success",
        source_evidence="None",
    )
    is_valid, reason = validator.validate_scenario(fake_scenario)
    assert is_valid is False
    assert "No implemented endpoint matches" in reason


def test_validator_rejects_unsupported_method():
    validator = TestScenarioValidator(discover_incidentflow_features())

    # DELETE /health does not exist
    scenario = ProposedTestScenario(
        feature_name="System Health Check",
        test_name="test_delete_health",
        test_objective="Try deleting health",
        target_endpoint="/health",
        http_method="DELETE",
        category="SystemHealth",
        test_steps=["DELETE /health"],
        input_data={},
        expected_status_code=200,
        expected_behavior="Fail",
        source_evidence="main.py",
    )
    is_valid, reason = validator.validate_scenario(scenario)
    assert is_valid is False
    assert "No implemented endpoint matches" in reason


def test_validator_rejects_empty_fields():
    validator = TestScenarioValidator(discover_incidentflow_features())

    scenario = ProposedTestScenario(
        feature_name="System Health Check",
        test_name="   ",  # Empty
        test_objective="Goal",
        target_endpoint="/health",
        http_method="GET",
        category="SystemHealth",
        test_steps=[],
        input_data={},
        expected_status_code=200,
        expected_behavior="Behavior",
        source_evidence="main.py",
    )
    is_valid, reason = validator.validate_scenario(scenario)
    assert is_valid is False
    assert "empty test_name" in reason

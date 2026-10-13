"""Unit tests for test catalogue, fingerprinting, and round-robin selection."""

import pytest
from incidentflow_testkit.ai_generator import ProposedTestScenario
from incidentflow_testkit.test_catalogue import (
    TestCatalogue,
    compute_scenario_fingerprint,
)


def test_stable_fingerprint_identical_on_superficial_rename():
    """Verify that changing test_name does not change the semantic fingerprint."""
    sc1 = ProposedTestScenario(
        feature_name="System Health Check",
        test_name="test_health_probe_alpha",
        test_objective="Verify health endpoint",
        target_endpoint="/health",
        http_method="GET",
        category="SystemHealth",
        test_steps=["GET /health"],
        input_data={},
        expected_status_code=200,
        expected_behavior="Status ok",
        source_evidence="main.py",
    )
    sc2 = ProposedTestScenario(
        feature_name="System Health Check",
        test_name="test_health_probe_beta_renamed",  # Different name
        test_objective="Verify health endpoint with different wording",
        target_endpoint="/health",
        http_method="GET",
        category="SystemHealth",
        test_steps=["GET /health"],
        input_data={},
        expected_status_code=200,
        expected_behavior="Status ok",
        source_evidence="main.py",
    )

    fp1 = compute_scenario_fingerprint(sc1)
    fp2 = compute_scenario_fingerprint(sc2)
    assert fp1 == fp2, "Superficial rename must produce the exact same fingerprint"


def test_batch_limit_and_deduplication(test_settings, sample_scenarios):
    """Verify batch limit enforcement and duplicate filtering within batch."""
    catalogue = TestCatalogue(test_settings)

    # Duplicate the list to test internal deduplication
    doubled = sample_scenarios + sample_scenarios
    batch, note = catalogue.select_batch(doubled, model_name="llama3:latest", limit=5)

    assert len(batch.scenarios) == 5
    # Check all fingerprints in batch are unique
    fingerprints = [s.fingerprint for s in batch.scenarios]
    assert len(fingerprints) == len(set(fingerprints))


def test_round_robin_selection_across_features(test_settings, sample_scenarios):
    """Verify round-robin picks distinct categories."""
    catalogue = TestCatalogue(test_settings)
    batch, note = catalogue.select_batch(sample_scenarios, model_name="llama3:latest", limit=3)

    assert len(batch.scenarios) == 3
    categories = [s.scenario.category for s in batch.scenarios]
    # Each scenario in the top 3 should come from a different category
    assert len(set(categories)) == 3


def test_history_persistence_and_cycle_rotation(test_settings, sample_scenarios):
    """Verify history file is written and second generation skips previously seen fingerprints."""
    catalogue1 = TestCatalogue(test_settings)
    batch1, _ = catalogue1.select_batch(sample_scenarios[:3], model_name="llama3:latest", limit=3)
    assert len(batch1.scenarios) == 3

    # Load new catalogue instance pointing to the same history file
    catalogue2 = TestCatalogue(test_settings)
    assert len(catalogue2.history.seen_fingerprints) == 3

    # Now pass all 6 sample scenarios. The first 3 should be skipped as already seen!
    batch2, note = catalogue2.select_batch(sample_scenarios, model_name="llama3:latest", limit=3)
    assert len(batch2.scenarios) == 3

    # None of batch2's fingerprints should be in batch1's fingerprints
    fp_batch1 = {s.fingerprint for s in batch1.scenarios}
    fp_batch2 = {s.fingerprint for s in batch2.scenarios}
    assert fp_batch1.isdisjoint(fp_batch2), "Consecutive generations must prefer fresh scenarios"

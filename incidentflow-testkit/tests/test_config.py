"""Unit tests for testkit configuration and safety constraints."""

import pytest
from incidentflow_testkit.config import TestkitSettings


def test_default_config_initialization():
    settings = TestkitSettings()
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.ollama_model == "llama3:latest"
    assert 1 <= settings.max_tests_per_batch <= 10
    assert "sqlite" in settings.test_database_url


def test_safety_rejects_production_database():
    """Verify that targeting production database is strictly rejected."""
    with pytest.raises(ValueError, match="CRITICAL SAFETY VIOLATION"):
        TestkitSettings(
            test_database_url="postgresql+asyncpg://postgres:12345@localhost:5432/incident_warroom"
        )

    with pytest.raises(ValueError, match="CRITICAL SAFETY VIOLATION"):
        TestkitSettings(
            test_database_url="postgresql+psycopg://postgres:secret@127.0.0.1:5432/incident_warroom"
        )


def test_safety_permits_isolated_test_databases():
    """Verify that isolated test databases are permitted."""
    s1 = TestkitSettings(test_database_url="sqlite+aiosqlite:///:memory:")
    assert "sqlite" in s1.test_database_url

    s2 = TestkitSettings(
        test_database_url="postgresql+asyncpg://postgres:pass@localhost:5432/incident_warroom_test"
    )
    assert s2.test_database_url.endswith("incident_warroom_test")


def test_batch_limit_bounds():
    """Verify batch limit constraints."""
    s = TestkitSettings(max_tests_per_batch=10)
    assert s.max_tests_per_batch == 10

    with pytest.raises(ValueError):
        TestkitSettings(max_tests_per_batch=0)

    with pytest.raises(ValueError):
        TestkitSettings(max_tests_per_batch=15)

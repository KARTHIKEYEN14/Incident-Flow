"""Configuration management and safety constraints for the IncidentFlow Testkit."""

import os
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TestkitSettings(BaseSettings):
    __test__ = False

    model_config = SettingsConfigDict(
        env_file=(".env", "incidentflow-testkit/.env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Local Ollama configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3:latest"
    ollama_timeout_seconds: int = 90

    # Generation controls: up to 10 test cases, default 5
    max_tests_per_batch: int = Field(default=5, ge=1, le=10)

    # Test database URL (must be isolated, defaults to in-memory SQLite)
    test_database_url: str = "sqlite+aiosqlite:///:memory:"

    # Paths
    testkit_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    incidentflow_backend_path: str = Field(default="../backend")

    @field_validator("test_database_url")
    @classmethod
    def validate_test_database_safety(cls, v: str) -> str:
        """Enforce strict protection against targeting the production database."""
        v_clean = v.strip().lower()
        prod_signatures = [
            "incident_warroom",  # Production database name
            "localhost:5432/incident_warroom",
            "127.0.0.1:5432/incident_warroom",
        ]
        # Allow test database like incident_warroom_test
        for sig in prod_signatures:
            if sig in v_clean and not v_clean.endswith("_test") and "_test" not in v_clean:
                raise ValueError(
                    f"CRITICAL SAFETY VIOLATION: Test database URL '{v}' appears to target "
                    f"the production database! Automated tests require an isolated test database "
                    f"(e.g. 'sqlite+aiosqlite:///:memory:' or a dedicated '_test' database)."
                )
        return v

    @property
    def backend_dir(self) -> Path:
        """Resolve absolute path to backend directory."""
        candidate = Path(self.incidentflow_backend_path)
        if not candidate.is_absolute():
            candidate = (self.testkit_root / candidate).resolve()
        if not candidate.exists():
            # Try repo root fallback
            alt = (self.testkit_root.parent / "backend").resolve()
            if alt.exists():
                return alt
        return candidate

    @property
    def generated_dir(self) -> Path:
        """Directory for generated test batches, history, and reports."""
        path = self.testkit_root / "generated"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def history_file(self) -> Path:
        return self.generated_dir / "generation_history.json"

    @property
    def latest_batch_file(self) -> Path:
        return self.generated_dir / "latest_batch.json"

    @property
    def latest_report_file(self) -> Path:
        return self.generated_dir / "latest_report.json"


_settings_instance: TestkitSettings | None = None


def get_settings() -> TestkitSettings:
    """Return singleton TestkitSettings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = TestkitSettings()
    return _settings_instance


def reset_settings() -> None:
    """Reset cached settings (useful in tests)."""
    global _settings_instance
    _settings_instance = None

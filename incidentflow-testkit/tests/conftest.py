import sys
from pathlib import Path
import pytest

testkit_dir = Path(__file__).resolve().parent.parent
if str(testkit_dir) not in sys.path:
    sys.path.insert(0, str(testkit_dir))

from incidentflow_testkit.config import TestkitSettings, reset_settings
from incidentflow_testkit.ai_generator import ProposedTestScenario
from incidentflow_testkit.feature_discovery import discover_incidentflow_features


@pytest.fixture
def test_settings(tmp_path: Path):
    """Provide isolated TestkitSettings pointing to temporary generated directory."""
    reset_settings()
    settings = TestkitSettings(
        testkit_root=tmp_path,
        incidentflow_backend_path=str(Path(__file__).resolve().parent.parent.parent / "backend"),
        test_database_url="sqlite+aiosqlite:///:memory:",
        max_tests_per_batch=5,
        ollama_model="llama3:latest",
    )
    return settings


@pytest.fixture
def sample_scenarios() -> list[ProposedTestScenario]:
    """Provide sample valid proposed scenarios across multiple categories."""
    return [
        ProposedTestScenario(
            feature_name="System Health Check",
            test_name="test_health_probe_returns_ok",
            test_objective="Verify public health probe returns 200 OK",
            target_endpoint="/health",
            http_method="GET",
            category="SystemHealth",
            test_steps=["Send GET /health"],
            input_data={},
            expected_status_code=200,
            expected_behavior="Status ok in response",
            source_evidence="GET /health route in main.py",
        ),
        ProposedTestScenario(
            feature_name="Departments Registry",
            test_name="test_departments_listing",
            test_objective="Verify departments list returns active departments",
            target_endpoint="/api/v1/auth/departments",
            http_method="GET",
            category="Departments",
            test_steps=["Send GET /api/v1/auth/departments"],
            input_data={},
            expected_status_code=200,
            expected_behavior="List of DepartmentResponse objects",
            source_evidence="GET /api/v1/auth/departments in auth.py",
        ),
        ProposedTestScenario(
            feature_name="User Authentication & Profiles",
            test_name="test_me_profile_unauthorized_without_token",
            test_objective="Verify /auth/me returns 401 when token is missing",
            target_endpoint="/api/v1/auth/me",
            http_method="GET",
            category="Authentication",
            test_steps=["Send GET /api/v1/auth/me without Authorization header"],
            input_data={},
            expected_status_code=401,
            expected_behavior="HTTP 401 Unauthorized",
            source_evidence="get_current_user_id in security.py",
        ),
        ProposedTestScenario(
            feature_name="OCC Guard & Lifecycle Transitions",
            test_name="test_status_update_with_stale_version_conflict",
            test_objective="Verify status update returns 409 Conflict when version mismatches",
            target_endpoint="/api/v1/incidents/{incident_id}/status",
            http_method="PATCH",
            category="OptimisticConcurrency",
            test_steps=["Send PATCH with version=999"],
            input_data={"status": "IDENTIFIED", "version": 999},
            expected_status_code=409,
            expected_behavior="HTTP 409 Conflict",
            source_evidence="_check_occ in incident_service.py",
        ),
        ProposedTestScenario(
            feature_name="Participant Roster & In-Room Messaging",
            test_name="test_post_room_message_success",
            test_objective="Verify valid room message posting",
            target_endpoint="/api/v1/incidents/{incident_id}/messages",
            http_method="POST",
            category="Collaboration",
            test_steps=["Send POST message body"],
            input_data={"body": "Investigating upstream gateway 504"},
            expected_status_code=201,
            expected_behavior="HTTP 201 Created with message payload",
            source_evidence="post_message in incident_service.py",
        ),
        ProposedTestScenario(
            feature_name="Immutable Audit Trail",
            test_name="test_get_audit_events_stream",
            test_objective="Verify audit events query returns chronological event log",
            target_endpoint="/api/v1/incidents/{incident_id}/events",
            http_method="GET",
            category="AuditEvents",
            test_steps=["Send GET events"],
            input_data={},
            expected_status_code=200,
            expected_behavior="Event list returned",
            source_evidence="list_events in incident_service.py",
        ),
    ]

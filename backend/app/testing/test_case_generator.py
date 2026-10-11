"""Automated Test Case Generation Engine for IncidentFlow.

Generates structured, executable test definitions mapped to verified implemented features.
Uses schema boundary analysis, status-transition matrices, role-based permission matrices,
and optimistic concurrency control rules.

Generation method:
Rule-Based Test Matrix Scaffolding + Schema Introspection Engine.
"""

import hashlib
import json
from typing import Any

from app.testing.feature_discovery import discover_features
from app.testing.schemas import TestCaseDefinition
from app.testing.test_validation import validate_test_suite

GENERATOR_VERSION = "1.0.0"


def generate_incidentflow_tests() -> list[TestCaseDefinition]:
    """Generate comprehensive, verified test definitions for all implemented features."""
    tests: list[TestCaseDefinition] = []

    # -------------------------------------------------------------------------
    # 1. Department Directory
    # -------------------------------------------------------------------------
    tests.append(
        TestCaseDefinition(
            id="TC-FUNC-DEPT-001",
            test_key="department_list_success",
            feature_name="Department Directory",
            category="FUNCTIONAL",
            title="Retrieve Available Employee Departments",
            description="Verify GET /api/v1/auth/departments returns active company departments with valid IDs and names.",
            source_evidence={"endpoint": "/api/v1/auth/departments", "method": "GET", "model": "Department"},
            preconditions=["Application and database are accessible."],
            test_steps=[
                "Send GET request to /api/v1/auth/departments.",
                "Verify HTTP response status is 200 OK.",
                "Verify response is a non-empty list of department objects containing 'id' and 'name'.",
            ],
            input_data={},
            expected_outcome={"status_code": 200, "is_list": True, "required_fields": ["id", "name"]},
            generator_version=GENERATOR_VERSION,
        )
    )

    # -------------------------------------------------------------------------
    # 2. User Registration & Authentication
    # -------------------------------------------------------------------------
    tests.append(
        TestCaseDefinition(
            id="TC-FUNC-AUTH-001",
            test_key="auth_register_success",
            feature_name="User Registration & Authentication",
            category="FUNCTIONAL",
            title="Register New User Account with Valid Department",
            description="Verify POST /api/v1/auth/register creates a new user, hashes password, and returns 201 Created.",
            source_evidence={"endpoint": "/api/v1/auth/register", "method": "POST", "schema": "UserCreate"},
            preconditions=["Valid department UUID is available."],
            test_steps=[
                "Generate unique user email and name.",
                "Send POST request to /api/v1/auth/register with name, email, password, and department_id.",
                "Verify HTTP response status is 201 Created.",
                "Verify returned object contains id, email, name, and department.",
            ],
            input_data={"password_length": 10},
            expected_outcome={"status_code": 201, "required_fields": ["id", "email", "name", "department"]},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-FUNC-AUTH-002",
            test_key="auth_login_success",
            feature_name="User Registration & Authentication",
            category="FUNCTIONAL",
            title="User Login and JWT Issuance",
            description="Verify POST /api/v1/auth/login with valid credentials returns 200 OK and bearer JWT access_token.",
            source_evidence={"endpoint": "/api/v1/auth/login", "method": "POST", "schema": "LoginRequest"},
            preconditions=["A registered test user exists."],
            test_steps=[
                "Send POST request to /api/v1/auth/login with correct email and password.",
                "Verify HTTP response status is 200 OK.",
                "Verify response contains access_token and token_type == 'bearer'.",
            ],
            input_data={},
            expected_outcome={"status_code": 200, "token_type": "bearer", "has_access_token": True},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-FUNC-AUTH-003",
            test_key="auth_get_me_success",
            feature_name="User Registration & Authentication",
            category="AUTHENTICATION",
            title="Retrieve Current Authenticated User Profile",
            description="Verify GET /api/v1/auth/me returns the profile of the caller identified by Bearer JWT token.",
            source_evidence={"endpoint": "/api/v1/auth/me", "method": "GET", "schema": "UserResponse"},
            preconditions=["Valid JWT access token is provided in Authorization header."],
            test_steps=[
                "Send GET request to /api/v1/auth/me with Bearer token.",
                "Verify HTTP response status is 200 OK.",
                "Verify returned email matches the authenticated user.",
            ],
            input_data={},
            expected_outcome={"status_code": 200, "required_fields": ["id", "email", "name"]},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-VAL-AUTH-001",
            test_key="auth_register_duplicate_email",
            feature_name="User Registration & Authentication",
            category="VALIDATION",
            title="Reject Duplicate User Email Registration",
            description="Verify POST /api/v1/auth/register returns HTTP 409 Conflict when attempting to register an already taken email.",
            source_evidence={"endpoint": "/api/v1/auth/register", "method": "POST", "constraint": "uq_users_email"},
            preconditions=["A user with the specified email already exists in the test DB."],
            test_steps=[
                "Send POST request to /api/v1/auth/register using the existing email address.",
                "Verify HTTP response status is 409 Conflict.",
                "Verify response detail indicates email is already registered.",
            ],
            input_data={},
            expected_outcome={"status_code": 409, "error_contains": "already registered"},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-VAL-AUTH-002",
            test_key="auth_register_invalid_department",
            feature_name="User Registration & Authentication",
            category="VALIDATION",
            title="Reject Registration with Non-existent Department",
            description="Verify POST /api/v1/auth/register returns HTTP 400 Bad Request when department_id does not exist.",
            source_evidence={"endpoint": "/api/v1/auth/register", "method": "POST", "model": "Department"},
            preconditions=["None."],
            test_steps=[
                "Send POST request to /api/v1/auth/register with a random non-existent UUID as department_id.",
                "Verify HTTP response status is 400 Bad Request.",
            ],
            input_data={"department_id": "00000000-0000-0000-0000-000000000000"},
            expected_outcome={"status_code": 400, "error_contains": "department does not exist"},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-AUTH-001",
            test_key="auth_login_invalid_password",
            feature_name="User Registration & Authentication",
            category="AUTHENTICATION",
            title="Reject Login with Incorrect Password",
            description="Verify POST /api/v1/auth/login returns HTTP 401 Unauthorized when password does not match.",
            source_evidence={"endpoint": "/api/v1/auth/login", "method": "POST"},
            preconditions=["A registered test user exists."],
            test_steps=[
                "Send POST request to /api/v1/auth/login with valid email but wrong password.",
                "Verify HTTP response status is 401 Unauthorized.",
            ],
            input_data={"password": "IncorrectPassword123!"},
            expected_outcome={"status_code": 401, "error_contains": "Invalid email or password"},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-AUTH-002",
            test_key="auth_missing_token_rejection",
            feature_name="User Registration & Authentication",
            category="AUTHENTICATION",
            title="Reject Protected Endpoint Request Without Credentials",
            description="Verify accessing /api/v1/auth/me without an Authorization header is rejected by HTTPBearer with HTTP 403 Forbidden.",
            source_evidence={"endpoint": "/api/v1/auth/me", "method": "GET", "dependency": "get_current_user_id"},
            preconditions=["None."],
            test_steps=[
                "Send GET request to /api/v1/auth/me without Authorization header.",
                "Verify HTTP response status is 403 Forbidden (Not authenticated).",
            ],
            input_data={},
            expected_outcome={"status_code": 403},
            generator_version=GENERATOR_VERSION,
        )
    )

    # -------------------------------------------------------------------------
    # 3. Incident Creation & Lifecycle Management
    # -------------------------------------------------------------------------
    tests.append(
        TestCaseDefinition(
            id="TC-FUNC-INC-001",
            test_key="incident_creation_success",
            feature_name="Incident Creation & Lifecycle Management",
            category="FUNCTIONAL",
            title="Declare Incident with Initial Version and Commander",
            description="Verify POST /api/v1/incidents creates an incident with version=1, status=INVESTIGATING, and creator as commander.",
            source_evidence={"endpoint": "/api/v1/incidents", "method": "POST", "schema": "IncidentCreate"},
            preconditions=["Authenticated user."],
            test_steps=[
                "Send POST request to /api/v1/incidents with title, service_name, and severity SEV-2.",
                "Verify HTTP response status is 201 Created.",
                "Verify incident status is INVESTIGATING.",
                "Verify incident version is 1.",
                "Verify creator is assigned as commander.",
            ],
            input_data={"title": "Primary Database Latency Spike", "service_name": "db-cluster-01", "severity": "SEV-2"},
            expected_outcome={"status_code": 201, "status": "INVESTIGATING", "version": 1, "severity": "SEV-2"},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-FUNC-INC-002",
            test_key="incident_get_by_id_success",
            feature_name="Incident Creation & Lifecycle Management",
            category="FUNCTIONAL",
            title="Retrieve Incident Details by UUID",
            description="Verify GET /api/v1/incidents/{incident_id} retrieves accurate incident details.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}", "method": "GET"},
            preconditions=["An incident exists that caller can view."],
            test_steps=[
                "Send GET request to /api/v1/incidents/{incident_id}.",
                "Verify HTTP response status is 200 OK.",
                "Verify returned incident ID matches request parameter.",
            ],
            input_data={},
            expected_outcome={"status_code": 200, "required_fields": ["id", "title", "service_name", "status", "version"]},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-VAL-INC-001",
            test_key="incident_create_invalid_severity",
            feature_name="Incident Creation & Lifecycle Management",
            category="VALIDATION",
            title="Reject Incident Creation with Invalid Severity Rating",
            description="Verify POST /api/v1/incidents returns HTTP 422 Unprocessable Entity when severity is not in [SEV-1..SEV-4].",
            source_evidence={"endpoint": "/api/v1/incidents", "method": "POST", "model": "SeverityLevel"},
            preconditions=["Authenticated user."],
            test_steps=[
                "Send POST request to /api/v1/incidents with severity='SEV-99'.",
                "Verify HTTP response status is 422 Unprocessable Entity.",
            ],
            input_data={"title": "Invalid Severity Test", "service_name": "test-svc", "severity": "SEV-99"},
            expected_outcome={"status_code": 422},
            generator_version=GENERATOR_VERSION,
        )
    )

    # -------------------------------------------------------------------------
    # 4. Visibility & Role-Based Access Control
    # -------------------------------------------------------------------------
    tests.append(
        TestCaseDefinition(
            id="TC-AUTHZ-VIS-001",
            test_key="visibility_organization_accessible_to_all",
            feature_name="Incident Visibility & Role-Based Access Control",
            category="AUTHORIZATION",
            title="Organization-Scoped Incident Accessible Across Departments",
            description="Verify that an incident with visibility='ORGANIZATION' can be viewed by an employee from any department.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}", "method": "GET", "visibility": "ORGANIZATION"},
            preconditions=["Incident with ORGANIZATION visibility exists.", "User from a different department."],
            test_steps=[
                "Authenticate as user in 'Finance' department.",
                "Send GET request for an incident created by 'Engineering' with ORGANIZATION visibility.",
                "Verify HTTP response status is 200 OK.",
            ],
            input_data={},
            expected_outcome={"status_code": 200},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-AUTHZ-VIS-002",
            test_key="visibility_department_forbidden_to_outsiders",
            feature_name="Incident Visibility & Role-Based Access Control",
            category="AUTHORIZATION",
            title="Department-Scoped Incident Blocked for Other Departments",
            description="Verify GET /api/v1/incidents/{incident_id} returns HTTP 403 Forbidden when a user outside the department attempts to view.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}", "method": "GET", "visibility": "DEPARTMENT"},
            preconditions=["Incident scoped to 'Security' department.", "User in 'Finance' department not assigned as participant."],
            test_steps=[
                "Authenticate as user in 'Finance'.",
                "Send GET request for department-scoped incident belonging to 'Security'.",
                "Verify HTTP response status is 403 Forbidden.",
            ],
            input_data={},
            expected_outcome={"status_code": 403, "error_contains": "Access denied"},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-AUTHZ-VIS-003",
            test_key="visibility_restricted_forbidden_to_uninvited",
            feature_name="Incident Visibility & Role-Based Access Control",
            category="AUTHORIZATION",
            title="Restricted Incident Blocked for Uninvited Employees",
            description="Verify GET /api/v1/incidents/{incident_id} returns HTTP 403 Forbidden for RESTRICTED incidents when caller is not invited.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}", "method": "GET", "visibility": "RESTRICTED"},
            preconditions=["RESTRICTED incident exists.", "Uninvited test user."],
            test_steps=[
                "Authenticate as uninvited user.",
                "Send GET request to view the RESTRICTED incident.",
                "Verify HTTP response status is 403 Forbidden.",
            ],
            input_data={},
            expected_outcome={"status_code": 403, "error_contains": "Access denied"},
            generator_version=GENERATOR_VERSION,
        )
    )

    # -------------------------------------------------------------------------
    # 5. Incident Status Transitions & Finite State Machine
    # -------------------------------------------------------------------------
    tests.append(
        TestCaseDefinition(
            id="TC-FUNC-STAT-001",
            test_key="status_transition_investigating_to_identified",
            feature_name="Incident Status Transitions & Finite State Machine",
            category="FUNCTIONAL",
            title="Valid Status Transition: INVESTIGATING -> IDENTIFIED",
            description="Verify PATCH /api/v1/incidents/{incident_id}/status allows moving from INVESTIGATING to IDENTIFIED and increments version.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}/status", "method": "PATCH", "state_machine": "VALID_STATUS_TRANSITIONS"},
            preconditions=["Incident in INVESTIGATING state with current version=1.", "User is commander/responder."],
            test_steps=[
                "Send PATCH /api/v1/incidents/{incident_id}/status with status='IDENTIFIED' and version=1.",
                "Verify HTTP response status is 200 OK.",
                "Verify returned status is IDENTIFIED.",
                "Verify version has incremented to 2.",
            ],
            input_data={"status": "IDENTIFIED", "version": 1},
            expected_outcome={"status_code": 200, "status": "IDENTIFIED", "version": 2},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-VAL-STAT-001",
            test_key="status_transition_invalid_jump_rejected",
            feature_name="Incident Status Transitions & Finite State Machine",
            category="VALIDATION",
            title="Reject Disallowed Status State Machine Transition",
            description="Verify PATCH /api/v1/incidents/{incident_id}/status returns HTTP 422 Unprocessable Entity when attempting a forbidden transition.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}/status", "method": "PATCH"},
            preconditions=["Incident in IDENTIFIED status with current version.", "User is commander."],
            test_steps=[
                "Attempt transition from IDENTIFIED back to INVESTIGATING (disallowed in state machine).",
                "Verify HTTP response status is 422 Unprocessable Entity.",
                "Verify error details state invalid status transition.",
            ],
            input_data={"status": "INVESTIGATING"},
            expected_outcome={"status_code": 422, "error_contains": "Invalid status transition"},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-FUNC-RES-001",
            test_key="incident_resolve_success",
            feature_name="Incident Status Transitions & Finite State Machine",
            category="FUNCTIONAL",
            title="Resolve Active Incident with Resolution Note",
            description="Verify POST /api/v1/incidents/{incident_id}/resolve transitions incident to RESOLVED and records resolved_at.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}/resolve", "method": "POST", "schema": "ResolveRequest"},
            preconditions=["Active incident in INVESTIGATING/IDENTIFIED/MONITORING status."],
            test_steps=[
                "Send POST request to /api/v1/incidents/{incident_id}/resolve with version and resolution_note.",
                "Verify HTTP response status is 200 OK.",
                "Verify status is RESOLVED.",
                "Verify resolved_at timestamp is populated.",
            ],
            input_data={"resolution_note": "Root cause mitigated via rollback to v2.4.1."},
            expected_outcome={"status_code": 200, "status": "RESOLVED", "has_resolved_at": True},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-VAL-RES-001",
            test_key="incident_resolve_already_resolved_rejected",
            feature_name="Incident Status Transitions & Finite State Machine",
            category="VALIDATION",
            title="Reject Resolving an Already Resolved Incident",
            description="Verify POST /api/v1/incidents/{incident_id}/resolve returns HTTP 422 when incident is already in RESOLVED state.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}/resolve", "method": "POST"},
            preconditions=["Incident already marked as RESOLVED."],
            test_steps=[
                "Send POST request to resolve the already resolved incident.",
                "Verify HTTP response status is 422 Unprocessable Entity.",
            ],
            input_data={"resolution_note": "Attempt duplicate resolve."},
            expected_outcome={"status_code": 422, "error_contains": "already resolved"},
            generator_version=GENERATOR_VERSION,
        )
    )

    # -------------------------------------------------------------------------
    # 6. Optimistic Concurrency Control (OCC)
    # -------------------------------------------------------------------------
    tests.append(
        TestCaseDefinition(
            id="TC-OCC-STAT-001",
            test_key="occ_status_update_conflict_detection",
            feature_name="Optimistic Concurrency Control (OCC)",
            category="CONCURRENCY",
            title="OCC Conflict on Stale Version Status Update",
            description="Verify PATCH /api/v1/incidents/{incident_id}/status returns HTTP 409 Conflict when client sends an outdated version number.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}/status", "method": "PATCH", "occ_function": "_check_occ"},
            preconditions=["Incident currently at version 2 (or higher)."],
            test_steps=[
                "Send PATCH status update with stale version=1.",
                "Verify HTTP response status is 409 Conflict.",
                "Verify response indicates version mismatch and conflict.",
            ],
            input_data={"status": "MONITORING", "version": 1},
            expected_outcome={"status_code": 409, "error_contains": "Conflict"},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-OCC-SEV-001",
            test_key="occ_severity_update_conflict_detection",
            feature_name="Optimistic Concurrency Control (OCC)",
            category="CONCURRENCY",
            title="OCC Conflict on Stale Version Severity Update",
            description="Verify PATCH /api/v1/incidents/{incident_id}/severity returns HTTP 409 Conflict when client sends an outdated version number.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}/severity", "method": "PATCH", "occ_function": "_check_occ"},
            preconditions=["Incident at version >= 2."],
            test_steps=[
                "Send PATCH severity update with obsolete version.",
                "Verify HTTP response status is 409 Conflict.",
            ],
            input_data={"severity": "SEV-1", "version": 1},
            expected_outcome={"status_code": 409, "error_contains": "Conflict"},
            generator_version=GENERATOR_VERSION,
        )
    )

    # -------------------------------------------------------------------------
    # 7. Severity Level Assessment & Upgrades
    # -------------------------------------------------------------------------
    tests.append(
        TestCaseDefinition(
            id="TC-FUNC-SEV-001",
            test_key="severity_update_success",
            feature_name="Severity Level Assessment & Upgrades",
            category="FUNCTIONAL",
            title="Update Incident Severity Rating and Increment Version",
            description="Verify PATCH /api/v1/incidents/{incident_id}/severity updates severity level from SEV-3 to SEV-1 and increments version.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}/severity", "method": "PATCH", "schema": "SeverityUpdate"},
            preconditions=["Active incident with valid current version.", "User has responder permissions."],
            test_steps=[
                "Send PATCH /api/v1/incidents/{incident_id}/severity with new severity SEV-1 and current version.",
                "Verify HTTP response status is 200 OK.",
                "Verify updated severity is SEV-1.",
                "Verify incident version incremented by 1.",
            ],
            input_data={"severity": "SEV-1"},
            expected_outcome={"status_code": 200, "severity": "SEV-1"},
            generator_version=GENERATOR_VERSION,
        )
    )

    # -------------------------------------------------------------------------
    # 8. Incident Roster & Participant Roles
    # -------------------------------------------------------------------------
    tests.append(
        TestCaseDefinition(
            id="TC-FUNC-PART-001",
            test_key="participant_add_responder_success",
            feature_name="Incident Roster & Participant Roles",
            category="FUNCTIONAL",
            title="Add Assigned Responder to Active Incident",
            description="Verify POST /api/v1/incidents/{incident_id}/participants enrolls a registered user with RESPONDER role.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}/participants", "method": "POST", "schema": "ParticipantAdd"},
            preconditions=["Incident exists.", "Second user exists who is not yet a participant."],
            test_steps=[
                "Send POST /api/v1/incidents/{incident_id}/participants with user_id and role='RESPONDER'.",
                "Verify HTTP response status is 201 Created.",
                "Verify participant role is RESPONDER.",
            ],
            input_data={"role": "RESPONDER"},
            expected_outcome={"status_code": 201, "role": "RESPONDER"},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-VAL-PART-001",
            test_key="participant_duplicate_rejected",
            feature_name="Incident Roster & Participant Roles",
            category="DATABASE_INTEGRITY",
            title="Reject Adding Duplicate Participant to Incident",
            description="Verify POST /api/v1/incidents/{incident_id}/participants returns HTTP 409 Conflict when user is already enrolled.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}/participants", "method": "POST", "constraint": "uq_incident_participant"},
            preconditions=["User is already a participant of the incident."],
            test_steps=[
                "Send POST request to add the same user a second time.",
                "Verify HTTP response status is 409 Conflict.",
                "Verify error message indicates user is already a participant.",
            ],
            input_data={"role": "OBSERVER"},
            expected_outcome={"status_code": 409, "error_contains": "already a participant"},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-AUTHZ-PART-001",
            test_key="observer_cannot_modify_incident",
            feature_name="Incident Roster & Participant Roles",
            category="AUTHORIZATION",
            title="Observer Role Denied Permission to Modify Incident Status",
            description="Verify that a user enrolled with OBSERVER role is denied permission (HTTP 403 Forbidden) when attempting to change status.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}/status", "method": "PATCH", "role": "OBSERVER"},
            preconditions=["User enrolled in incident with OBSERVER role."],
            test_steps=[
                "Authenticate as the observer user.",
                "Send PATCH /api/v1/incidents/{incident_id}/status attempting status change.",
                "Verify HTTP response status is 403 Forbidden.",
            ],
            input_data={"status": "IDENTIFIED"},
            expected_outcome={"status_code": 403, "error_contains": "Only incident commanders and responders"},
            generator_version=GENERATOR_VERSION,
        )
    )

    # -------------------------------------------------------------------------
    # 9. Incident War Room Messaging
    # -------------------------------------------------------------------------
    tests.append(
        TestCaseDefinition(
            id="TC-FUNC-MSG-001",
            test_key="message_post_and_list_success",
            feature_name="Incident War Room Messaging",
            category="FUNCTIONAL",
            title="Post Message to Incident War Room and List Messages",
            description="Verify POST /api/v1/incidents/{incident_id}/messages persists a message and GET /messages retrieves it.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}/messages", "method": "POST", "schema": "MessageCreate"},
            preconditions=["Incident exists and caller has viewing permission."],
            test_steps=[
                "Send POST /api/v1/incidents/{incident_id}/messages with body text.",
                "Verify HTTP response status is 201 Created with message id and author_name.",
                "Send GET /api/v1/incidents/{incident_id}/messages.",
                "Verify message appears in chronological message list.",
            ],
            input_data={"body": "Mitigation steps: Traffic rerouted to secondary cluster."},
            expected_outcome={"status_code": 201, "required_fields": ["id", "body", "author_id", "author_name"]},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-BND-MSG-001",
            test_key="message_body_boundary_limits",
            feature_name="Incident War Room Messaging",
            category="BOUNDARY",
            title="Enforce Upper Character Limit on Message Body",
            description="Verify that message body accepts up to 5000 characters and rejects messages exceeding 5000 characters with HTTP 422.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}/messages", "method": "POST", "schema": "MessageCreate.body"},
            preconditions=["Incident exists."],
            test_steps=[
                "Send message with exactly 5000 characters; verify 201 Created.",
                "Send message with 5001 characters; verify 422 Unprocessable Entity.",
            ],
            input_data={"max_length": 5000},
            expected_outcome={"status_code": 201, "boundary_rejection_code": 422},
            generator_version=GENERATOR_VERSION,
        )
    )

    # -------------------------------------------------------------------------
    # 10. Deterministic Audit Event Stream
    # -------------------------------------------------------------------------
    tests.append(
        TestCaseDefinition(
            id="TC-FUNC-EVT-001",
            test_key="audit_events_logged_and_ordered",
            feature_name="Deterministic Audit Event Stream",
            category="DATABASE_INTEGRITY",
            title="Verify Monotonic Ordering and Event Recording",
            description="Verify GET /api/v1/incidents/{incident_id}/events returns recorded events in deterministic ascending integer ID order.",
            source_evidence={"endpoint": "/api/v1/incidents/{incident_id}/events", "method": "GET", "model": "IncidentEvent"},
            preconditions=["Incident with creation and status change events exists."],
            test_steps=[
                "Send GET request to /api/v1/incidents/{incident_id}/events.",
                "Verify HTTP response status is 200 OK.",
                "Verify events contains INCIDENT_CREATED and subsequent event types.",
                "Verify event IDs are strictly monotonically increasing.",
            ],
            input_data={},
            expected_outcome={"status_code": 200, "is_ordered": True, "has_incident_created": True},
            generator_version=GENERATOR_VERSION,
        )
    )

    # -------------------------------------------------------------------------
    # 11. Real-Time WebSocket Gateway
    # -------------------------------------------------------------------------
    tests.append(
        TestCaseDefinition(
            id="TC-WS-AUTH-001",
            test_key="websocket_reject_unauthenticated_connection",
            feature_name="Real-Time WebSocket Gateway",
            category="REALTIME",
            title="Reject WebSocket Connection Without Valid JWT Token",
            description="Verify connecting to /ws/incidents/{id} without a token or with an invalid token closes with code 4003.",
            source_evidence={"endpoint": "/ws/incidents/{incident_id}", "method": "GET", "protocol": "WebSocket"},
            preconditions=["Active incident exists."],
            test_steps=[
                "Attempt WebSocket connection with token='invalid-fake-token'.",
                "Verify connection is closed with code 4003 (Authentication failed).",
            ],
            input_data={"token": "invalid_jwt_token_sample"},
            expected_outcome={"ws_close_code": 4003},
            generator_version=GENERATOR_VERSION,
        )
    )

    tests.append(
        TestCaseDefinition(
            id="TC-WS-PING-001",
            test_key="websocket_ping_pong_protocol",
            feature_name="Real-Time WebSocket Gateway",
            category="REALTIME",
            title="Verify WebSocket Ping-Pong Heartbeat Protocol",
            description="Verify authenticated WebSocket client sending JSON ping receives immediate JSON pong response.",
            source_evidence={"endpoint": "/ws/incidents/{incident_id}", "method": "GET", "protocol": "WebSocket"},
            preconditions=["Authenticated user with visibility rights."],
            test_steps=[
                "Establish authenticated WebSocket connection with ?token=<jwt>.",
                "Send text frame: '{\"type\": \"ping\"}'.",
                "Receive response frame and verify payload is '{\"type\": \"pong\"}'.",
            ],
            input_data={"type": "ping"},
            expected_outcome={"ws_connected": True, "received_type": "pong"},
            generator_version=GENERATOR_VERSION,
        )
    )

    # -------------------------------------------------------------------------
    # 12. System Health & Diagnostics
    # -------------------------------------------------------------------------
    tests.append(
        TestCaseDefinition(
            id="TC-REG-HLTH-001",
            test_key="system_health_liveness_check",
            feature_name="System Health & Diagnostics",
            category="REGRESSION",
            title="Liveness Health Probe Diagnostic Verification",
            description="Verify GET /health returns HTTP 200 OK and status 'ok'.",
            source_evidence={"endpoint": "/health", "method": "GET"},
            preconditions=["FastAPI server running."],
            test_steps=[
                "Send GET request to /health.",
                "Verify HTTP response status is 200 OK.",
                "Verify returned body contains status 'ok'.",
            ],
            input_data={},
            expected_outcome={"status_code": 200, "status": "ok"},
            generator_version=GENERATOR_VERSION,
        )
    )

    return tests


def generate_and_validate_suite() -> tuple[list[TestCaseDefinition], list[dict[str, Any]]]:
    """Generate all test cases and validate each against verified features."""
    inventory = discover_features()
    verified_names = {f.name for f in inventory.features}
    raw_tests = generate_incidentflow_tests()
    approved, errors = validate_test_suite(raw_tests, verified_names)
    return approved, errors


def compute_test_fingerprint(tc: TestCaseDefinition) -> str:
    """Compute stable, deterministic fingerprint based on feature, scenario, inputs, and expected outcome."""
    content = {
        "feature": tc.feature_name,
        "key": tc.test_key,
        "category": tc.category,
        "input": tc.input_data or {},
        "expected": tc.expected_outcome or {},
    }
    raw = json.dumps(content, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


# Curated round-robin sequence: 6 distinct batches of 5 tests covering all 12 verified features
ROUND_ROBIN_TEST_KEYS: list[str] = [
    # Batch 1 (Auth, Incident Creation, Status FSM, Department Visibility, War Room Messaging)
    "auth_login_success",
    "incident_creation_success",
    "status_transition_invalid_jump_rejected",
    "visibility_department_forbidden_to_outsiders",
    "message_post_and_list_success",

    # Batch 2 (Auth Credentials, Validation Boundaries, Roster Roles, WebSocket Protocol, OCC Status)
    "auth_login_invalid_password",
    "incident_create_invalid_severity",
    "observer_cannot_modify_incident",
    "websocket_ping_pong_protocol",
    "occ_status_update_conflict_detection",

    # Batch 3 (Department Directory, User Registration, FSM Resolution, Severity Upgrade, System Health)
    "department_list_success",
    "auth_register_success",
    "incident_resolve_success",
    "severity_update_success",
    "system_health_liveness_check",

    # Batch 4 (Registration Conflict, Incident Read, Participant Visibility, Staff Assignment, Message Limit)
    "auth_register_duplicate_email",
    "incident_get_by_id_success",
    "visibility_restricted_forbidden_to_uninvited",
    "participant_add_responder_success",
    "message_body_boundary_limits",

    # Batch 5 (Auth Profile, Resolution Guard, OCC Severity, Duplicate Roster, Audit Trail)
    "auth_get_me_success",
    "incident_resolve_already_resolved_rejected",
    "occ_severity_update_conflict_detection",
    "participant_duplicate_rejected",
    "audit_events_logged_and_ordered",

    # Batch 6 (Department Validation, Token Rejection, Organization Visibility, Status Investigation, WebSocket Auth)
    "auth_register_invalid_department",
    "auth_missing_token_rejection",
    "visibility_organization_accessible_to_all",
    "status_transition_investigating_to_identified",
    "websocket_reject_unauthenticated_connection",
]


def select_round_robin_batch(
    catalogue: list[TestCaseDefinition],
    history_fingerprints: list[str],
    batch_size: int = 5,
    last_batch_number: int = 0,
    last_round_number: int = 1,
) -> tuple[list[TestCaseDefinition], int, int, bool, list[str], str]:
    """Select the next batch of 5 distinct test cases using round-robin across features.

    Avoids duplicates within the batch and across recent batches in the current cycle.
    Restarts the cycle automatically when the scenario catalogue is exhausted.

    Returns:
        (batch_tests, batch_number, round_number, cycle_restarted, updated_history_fingerprints, message)
    """
    key_map = {t.test_key: t for t in catalogue}
    ordered_catalogue = [key_map[k] for k in ROUND_ROBIN_TEST_KEYS if k in key_map]
    # Append any remaining catalogue tests not explicitly listed in key sequence
    for t in catalogue:
        if t.test_key not in set(ROUND_ROBIN_TEST_KEYS):
            ordered_catalogue.append(t)

    seen_fingerprints = set(history_fingerprints)
    remaining_tests = [
        t for t in ordered_catalogue
        if compute_test_fingerprint(t) not in seen_fingerprints
    ]

    cycle_restarted = False
    round_number = max(1, last_round_number)

    # If all catalogue tests were generated in this round, start a fresh cycle
    if not remaining_tests:
        cycle_restarted = True
        round_number += 1
        history_fingerprints = []
        remaining_tests = ordered_catalogue
        batch_number = 1
    else:
        batch_number = last_batch_number + 1

    # Select up to batch_size tests from remaining
    batch_tests = remaining_tests[:batch_size]

    # Deduplicate within batch by ID and fingerprint (strictly distinct scenarios)
    seen_in_batch: set[str] = set()
    deduped_batch: list[TestCaseDefinition] = []
    for t in batch_tests:
        fp = compute_test_fingerprint(t)
        if t.id not in seen_in_batch and fp not in seen_in_batch:
            seen_in_batch.add(t.id)
            seen_in_batch.add(fp)
            deduped_batch.append(t)
    batch_tests = deduped_batch

    new_fps = [compute_test_fingerprint(t) for t in batch_tests]
    updated_history = history_fingerprints + new_fps

    total_catalogue = len(ordered_catalogue)
    if cycle_restarted:
        message = (
            f"Full scenario catalogue completed ({total_catalogue}/{total_catalogue} tests). "
            f"Restarting cycle: Round {round_number} · Batch {batch_number} ({len(batch_tests)} tests)."
        )
    elif len(batch_tests) < batch_size:
        message = (
            f"Generated Batch {batch_number}: only {len(batch_tests)} distinct test scenario(s) "
            f"available in this round. No invalid filler tests generated."
        )
    else:
        message = (
            f"Generated Batch {batch_number} · {len(batch_tests)} test cases across verified features."
        )

    return batch_tests, batch_number, round_number, cycle_restarted, updated_history, message


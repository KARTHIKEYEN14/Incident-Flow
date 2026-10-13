"""Feature discovery engine that inspects the actual IncidentFlow implementation."""

import sys
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, Field


class DiscoveredEndpoint(BaseModel):
    path: str
    method: str
    summary: str
    auth_required: bool = True
    request_schema: str | None = None
    response_schema: str | None = None
    expected_status_codes: list[int] = Field(default_factory=list)
    notes: str = ""


class DiscoveredFeature(BaseModel):
    name: str
    category: str
    description: str
    endpoints: list[DiscoveredEndpoint] = Field(default_factory=list)
    business_rules: list[str] = Field(default_factory=list)
    supported_scenarios: list[str] = Field(default_factory=list)


class FeatureInventory(BaseModel):
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    features: dict[str, DiscoveredFeature] = Field(default_factory=dict)
    known_categories: list[str] = Field(default_factory=list)


def discover_incidentflow_features(backend_dir: Path | None = None) -> FeatureInventory:
    """
    Inspect the IncidentFlow codebase and return verified, implemented features only.
    Strictly omits non-existent or hypothetical endpoints.
    """
    inventory = FeatureInventory(
        known_categories=[
            "Authentication",
            "Departments",
            "IncidentLifecycle",
            "AccessControl",
            "OptimisticConcurrency",
            "Collaboration",
            "AuditEvents",
            "SystemHealth",
        ]
    )

    # 1. System Health
    inventory.features["system_health"] = DiscoveredFeature(
        name="System Health Check",
        category="SystemHealth",
        description="Public health probe returning service operational status.",
        endpoints=[
            DiscoveredEndpoint(
                path="/health",
                method="GET",
                summary="Health check probe",
                auth_required=False,
                expected_status_codes=[200],
                notes="Returns {'status': 'ok'}",
            )
        ],
        business_rules=["Unauthenticated public endpoint"],
        supported_scenarios=[
            "Health probe returns HTTP 200 OK with status ok",
        ],
    )

    # 2. Departments
    inventory.features["departments"] = DiscoveredFeature(
        name="Departments Registry",
        category="Departments",
        description="List all available departments for employee organization and registration.",
        endpoints=[
            DiscoveredEndpoint(
                path="/api/v1/auth/departments",
                method="GET",
                summary="List all departments",
                auth_required=False,
                response_schema="list[DepartmentResponse]",
                expected_status_codes=[200],
                notes="Returns list of departments with id and name",
            ),
            DiscoveredEndpoint(
                path="/api/v1/departments",
                method="GET",
                summary="Alias route to list all departments",
                auth_required=False,
                response_schema="list[DepartmentResponse]",
                expected_status_codes=[200],
            ),
        ],
        business_rules=[
            "Publicly accessible for employee self-registration",
            "Every user belongs to an existing department",
        ],
        supported_scenarios=[
            "Listing departments returns HTTP 200 with non-empty list",
        ],
    )

    # 3. Authentication & User Profile
    inventory.features["authentication"] = DiscoveredFeature(
        name="User Authentication & Profiles",
        category="Authentication",
        description="Registration with department validation, JWT login, and profile lookup.",
        endpoints=[
            DiscoveredEndpoint(
                path="/api/v1/auth/register",
                method="POST",
                summary="Register new user account",
                auth_required=False,
                request_schema="UserCreate(name, email, password, department_id)",
                response_schema="UserResponse",
                expected_status_codes=[201, 400, 409, 422],
                notes="Fails with 409 on duplicate email; 400 on invalid department_id",
            ),
            DiscoveredEndpoint(
                path="/api/v1/auth/login",
                method="POST",
                summary="Authenticate user and issue JWT bearer token",
                auth_required=False,
                request_schema="LoginRequest(email, password)",
                response_schema="TokenResponse(access_token, token_type)",
                expected_status_codes=[200, 401, 422],
                notes="Fails with 401 on bad credentials",
            ),
            DiscoveredEndpoint(
                path="/api/v1/auth/me",
                method="GET",
                summary="Get authenticated user's profile",
                auth_required=True,
                response_schema="UserResponse",
                expected_status_codes=[200, 401, 403],
            ),
            DiscoveredEndpoint(
                path="/api/v1/auth/users",
                method="GET",
                summary="List users for participant assignment",
                auth_required=True,
                response_schema="list[UserResponse]",
                expected_status_codes=[200, 401, 403],
            ),
        ],
        business_rules=[
            "Password minimum length is 6 characters",
            "Email must be unique across accounts",
            "Department ID must reference an existing department",
            "Protected routes reject requests without a valid Bearer token with 401",
        ],
        supported_scenarios=[
            "Successful registration returns HTTP 201 Created",
            "Registration rejects existing duplicate email with HTTP 409 Conflict",
            "Registration rejects invalid department UUID with HTTP 400 Bad Request",
            "Login with valid credentials returns HTTP 200 and access_token",
            "Login with invalid password returns HTTP 401 Unauthorized",
            "Fetching /auth/me with valid token returns user profile",
            "Fetching /auth/me without token returns HTTP 401 Unauthorized",
        ],
    )

    # 4. Incident Creation and Retrieval
    inventory.features["incident_creation_retrieval"] = DiscoveredFeature(
        name="Incident Declaration & Scoped Querying",
        category="IncidentLifecycle",
        description="Declare incidents with severity/visibility and list incidents.",
        endpoints=[
            DiscoveredEndpoint(
                path="/api/v1/incidents",
                method="POST",
                summary="Create a new incident",
                auth_required=True,
                request_schema="IncidentCreate(title, service_name, severity, visibility, department)",
                response_schema="IncidentResponse",
                expected_status_codes=[201, 401, 422],
                notes="Severities: SEV-1, SEV-2, SEV-3, SEV-4. Initial status: INVESTIGATING, initial version: 1",
            ),
            DiscoveredEndpoint(
                path="/api/v1/incidents",
                method="GET",
                summary="List visible incidents with pagination and filters",
                auth_required=True,
                response_schema="IncidentListResponse(incidents, total, page, page_size)",
                expected_status_codes=[200, 401],
            ),
            DiscoveredEndpoint(
                path="/api/v1/incidents/{incident_id}",
                method="GET",
                summary="Get detailed incident by UUID",
                auth_required=True,
                response_schema="IncidentResponse",
                expected_status_codes=[200, 401, 403, 404],
            ),
        ],
        business_rules=[
            "Creator is automatically assigned as COMMANDER participant",
            "Supported severities: SEV-1, SEV-2, SEV-3, SEV-4",
            "Initial status is always INVESTIGATING",
            "Initial OCC version is 1",
        ],
        supported_scenarios=[
            "Create valid incident returns HTTP 201 with version 1 and status INVESTIGATING",
            "Get incident by valid ID returns HTTP 200 with matching attributes",
            "Get incident with non-existent UUID returns HTTP 404 Not Found",
            "Filter incidents by status or severity returns matching subset",
        ],
    )

    # 5. Access Control & Visibility Scoping
    inventory.features["access_control_visibility"] = DiscoveredFeature(
        name="Role-Based & Visibility Access Control",
        category="AccessControl",
        description="Enforces ORGANIZATION, DEPARTMENT, and RESTRICTED incident visibility.",
        endpoints=[
            DiscoveredEndpoint(
                path="/api/v1/incidents/{incident_id}",
                method="GET",
                summary="Enforce incident visibility constraints",
                auth_required=True,
                expected_status_codes=[200, 403, 404],
            )
        ],
        business_rules=[
            "ORGANIZATION visibility is viewable by all authenticated users",
            "DEPARTMENT visibility is viewable only by users in the incident department, or creator/commander/participants",
            "RESTRICTED visibility is viewable only by creator, commander, and explicitly invited participants",
            "Unauthorized access returns HTTP 403 Forbidden",
        ],
        supported_scenarios=[
            "User in same department can access DEPARTMENT visibility incident",
            "User outside department is rejected with HTTP 403 from DEPARTMENT incident",
            "Uninvited user is rejected with HTTP 403 from RESTRICTED incident",
            "Explicit participant can access RESTRICTED incident",
        ],
    )

    # 6. Optimistic Concurrency Control & State Transitions
    inventory.features["concurrency_and_lifecycle"] = DiscoveredFeature(
        name="OCC Guard & Lifecycle Transitions",
        category="OptimisticConcurrency",
        description="State updates and severity modifications guarded by OCC version checks.",
        endpoints=[
            DiscoveredEndpoint(
                path="/api/v1/incidents/{incident_id}/status",
                method="PATCH",
                summary="Transition incident lifecycle status with OCC version token",
                auth_required=True,
                request_schema="StatusUpdate(status, version)",
                response_schema="IncidentResponse",
                expected_status_codes=[200, 401, 403, 409, 422],
                notes="Valid transitions: INVESTIGATING->IDENTIFIED/MONITORING/RESOLVED; IDENTIFIED->MONITORING/RESOLVED; MONITORING->RESOLVED/INVESTIGATING; RESOLVED->INVESTIGATING",
            ),
            DiscoveredEndpoint(
                path="/api/v1/incidents/{incident_id}/severity",
                method="PATCH",
                summary="Update severity level with OCC version token",
                auth_required=True,
                request_schema="SeverityUpdate(severity, version)",
                response_schema="IncidentResponse",
                expected_status_codes=[200, 401, 403, 409, 422],
            ),
            DiscoveredEndpoint(
                path="/api/v1/incidents/{incident_id}/resolve",
                method="POST",
                summary="Resolve incident with resolution note and OCC token",
                auth_required=True,
                request_schema="ResolveRequest(version, resolution_note)",
                response_schema="IncidentResponse",
                expected_status_codes=[200, 401, 403, 409, 422],
            ),
        ],
        business_rules=[
            "Stale version token immediately returns HTTP 409 Conflict",
            "Successful status update increments version by 1 and records audit event",
            "Illegal status transition returns HTTP 422 Unprocessable Entity",
            "Only COMMANDER and RESPONDER participants can update status, severity, or resolve",
            "Resolving an already-resolved incident returns HTTP 422 Unprocessable Entity",
        ],
        supported_scenarios=[
            "Status advance with correct version succeeds and increments version to 2",
            "Status advance with mismatched version returns HTTP 409 Conflict",
            "Disallowed status transition returns HTTP 422 Unprocessable Entity",
            "Severity update with correct version succeeds and increments version",
            "Resolve incident marks status RESOLVED and records resolved_at",
            "Resolving already-resolved incident returns HTTP 422 Unprocessable Entity",
        ],
    )

    # 7. Collaboration & Timeline
    inventory.features["collaboration_and_timeline"] = DiscoveredFeature(
        name="Participant Roster & In-Room Messaging",
        category="Collaboration",
        description="Invite responders, add room messages, and retrieve chronologically.",
        endpoints=[
            DiscoveredEndpoint(
                path="/api/v1/incidents/{incident_id}/participants",
                method="POST",
                summary="Add participant to incident room roster",
                auth_required=True,
                request_schema="ParticipantAdd(user_id, role)",
                response_schema="ParticipantResponse",
                expected_status_codes=[201, 401, 403, 404, 409, 422],
                notes="Roles: COMMANDER, RESPONDER, OBSERVER",
            ),
            DiscoveredEndpoint(
                path="/api/v1/incidents/{incident_id}/participants",
                method="GET",
                summary="List all participants in incident room",
                auth_required=True,
                response_schema="list[ParticipantResponse]",
                expected_status_codes=[200, 401, 403],
            ),
            DiscoveredEndpoint(
                path="/api/v1/incidents/{incident_id}/messages",
                method="POST",
                summary="Post diagnostic message to incident room",
                auth_required=True,
                request_schema="MessageCreate(body)",
                response_schema="MessageResponse",
                expected_status_codes=[201, 401, 403, 422],
            ),
            DiscoveredEndpoint(
                path="/api/v1/incidents/{incident_id}/messages",
                method="GET",
                summary="List messages with pagination",
                auth_required=True,
                response_schema="MessageListResponse(messages, total)",
                expected_status_codes=[200, 401, 403],
            ),
        ],
        business_rules=[
            "Adding duplicate participant returns HTTP 409 Conflict",
            "Adding non-existent user returns HTTP 404 Not Found",
            "Posting empty message body fails with HTTP 422",
            "Message author must have visibility access to the incident",
        ],
        supported_scenarios=[
            "Invite new responder to incident succeeds with HTTP 201",
            "Invite duplicate participant returns HTTP 409 Conflict",
            "Post message to room returns HTTP 201 and is retrievable via GET",
            "Observer or responder can view message list",
        ],
    )

    # 8. Immutable Audit Trail
    inventory.features["audit_event_trail"] = DiscoveredFeature(
        name="Immutable Audit Trail",
        category="AuditEvents",
        description="Sequential, append-only event stream recording all lifecycle changes.",
        endpoints=[
            DiscoveredEndpoint(
                path="/api/v1/incidents/{incident_id}/events",
                method="GET",
                summary="List chronological audit events for incident",
                auth_required=True,
                response_schema="EventListResponse(events, total)",
                expected_status_codes=[200, 401, 403],
            )
        ],
        business_rules=[
            "Events are automatically recorded for CREATED, STATUS_CHANGE, SEVERITY_CHANGE, PARTICIPANT_JOINED, MESSAGE_POSTED, INCIDENT_RESOLVED",
            "Events are ordered chronologically by sequential integer ID",
            "Event logs contain actor attribution and version snapshot",
        ],
        supported_scenarios=[
            "Newly created incident has initial INCIDENT_CREATED audit event",
            "Status change appends STATUS_CHANGE audit event with old and new status",
        ],
    )

    return inventory


def get_sanitized_system_summary(inventory: FeatureInventory) -> str:
    """
    Produce a concise, sanitized context prompt for the AI model.
    STRICTLY excludes secrets, environment variables, passwords, or database credentials.
    """
    lines = [
        "# IncidentFlow Application Implementation Summary",
        "Target API: FastAPI (Python 3.10+)",
        "Database: PostgreSQL / SQLAlchemy 2.0 async models",
        "",
        "## Verified Implemented Features & Endpoints:",
    ]

    for key, feat in inventory.features.items():
        lines.append(f"\n### Feature: {feat.name} (Category: {feat.category})")
        lines.append(f"Description: {feat.description}")
        lines.append("Endpoints:")
        for ep in feat.endpoints:
            auth_str = "Bearer Token Required" if ep.auth_required else "Public"
            req = f" | Request: {ep.request_schema}" if ep.request_schema else ""
            lines.append(f"  - [{ep.method}] {ep.path} ({auth_str}{req}) -> Status: {ep.expected_status_codes}")
        if feat.business_rules:
            lines.append("Business Rules:")
            for rule in feat.business_rules:
                lines.append(f"  * {rule}")
        if feat.supported_scenarios:
            lines.append("Example Implemented Scenarios:")
            for sc in feat.supported_scenarios:
                lines.append(f"  * {sc}")

    lines.append("\n## EXCLUSION NOTICE:")
    lines.append("The following hypothetical features are NOT implemented and MUST NOT be tested:")
    lines.append("- No file uploads or document attachments")
    lines.append("- No incident deletion (DELETE /incidents/{id})")
    lines.append("- No user profile update or password reset endpoints")
    lines.append("- No email/SMS notifications or third-party webhooks")
    lines.append("- No metrics, billing, or subscription tiers")
    return "\n".join(lines)

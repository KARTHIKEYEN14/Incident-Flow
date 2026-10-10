"""Incident management service with OCC, status validation, and atomic event logging."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    EventType,
    Incident,
    IncidentEvent,
    IncidentMessage,
    IncidentParticipant,
    IncidentStatus,
    IncidentVisibility,
    ParticipantRole,
    SeverityLevel,
    User,
    VALID_STATUS_TRANSITIONS,
)


# ---------------------------------------------------------------------------
# Helpers & Permissions
# ---------------------------------------------------------------------------

def _validate_severity(value: str) -> SeverityLevel:
    try:
        return SeverityLevel(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid severity: {value}. Must be one of: {[s.value for s in SeverityLevel]}",
        )


def _validate_status(value: str) -> IncidentStatus:
    try:
        return IncidentStatus(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status: {value}. Must be one of: {[s.value for s in IncidentStatus]}",
        )


def _validate_role(value: str) -> ParticipantRole:
    try:
        return ParticipantRole(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role: {value}. Must be one of: {[r.value for r in ParticipantRole]}",
        )


def _validate_visibility(value: str) -> IncidentVisibility:
    try:
        return IncidentVisibility(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid visibility: {value}. Must be one of: {[v.value for v in IncidentVisibility]}",
        )


async def _get_incident_or_404(db: AsyncSession, incident_id: UUID) -> Incident:
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


async def can_view_incident(db: AsyncSession, incident: Incident, user: User) -> bool:
    """
    Check if a user has visibility/viewing access to an incident.
    - Creator & Commander always have access.
    - Explicit participants always have access (including invitees to RESTRICTED incidents).
    - ORGANIZATION: All authenticated users can view.
    - DEPARTMENT: Users in the affected department can view.
    - RESTRICTED: Only creator, commander, and explicitly invited participants can view.
    """
    if incident.creator_id == user.id or incident.commander_id == user.id:
        return True

    # Check if user is an explicit participant
    participant_res = await db.execute(
        select(IncidentParticipant).where(
            IncidentParticipant.incident_id == incident.id,
            IncidentParticipant.user_id == user.id,
        )
    )
    if participant_res.scalar_one_or_none() is not None:
        return True

    # Check visibility rules
    if incident.visibility == IncidentVisibility.ORGANIZATION:
        return True

    if incident.visibility == IncidentVisibility.DEPARTMENT:
        user_dept = (user.department or "").strip().lower()
        inc_dept = (incident.department or "").strip().lower()
        if user_dept and inc_dept and user_dept == inc_dept:
            return True

    return False


async def can_modify_incident(db: AsyncSession, incident: Incident, user: User) -> bool:
    """
    Check if a user has responder/commander permissions to modify or resolve an incident.
    Separates viewing permissions from responder permissions.
    Only creator, commander, or participants with COMMANDER or RESPONDER role can modify.
    """
    if incident.creator_id == user.id or incident.commander_id == user.id:
        return True

    participant_res = await db.execute(
        select(IncidentParticipant).where(
            IncidentParticipant.incident_id == incident.id,
            IncidentParticipant.user_id == user.id,
        )
    )
    participant = participant_res.scalar_one_or_none()
    if participant and participant.role in (ParticipantRole.COMMANDER, ParticipantRole.RESPONDER):
        return True

    return False


async def _check_occ(incident: Incident, expected_version: int) -> None:
    """Optimistic concurrency control check."""
    if incident.version != expected_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflict: incident version is {incident.version}, expected {expected_version}. Another responder has modified this incident.",
        )


def _add_event(
    db: AsyncSession,
    incident_id: UUID,
    actor_id: UUID,
    event_type: EventType,
    payload: dict | None = None,
    event_version: int | None = None,
) -> IncidentEvent:
    event = IncidentEvent(
        incident_id=incident_id,
        actor_id=actor_id,
        event_type=event_type,
        payload=payload,
        event_version=event_version,
    )
    db.add(event)
    return event


# ---------------------------------------------------------------------------
# Incident CRUD
# ---------------------------------------------------------------------------

async def create_incident(
    db: AsyncSession,
    title: str,
    description: str | None,
    service_name: str,
    severity: str,
    creator_id: UUID,
    commander_id: UUID | None = None,
    visibility: str = "ORGANIZATION",
    department: str | None = None,
) -> Incident:
    sev = _validate_severity(severity)
    vis = _validate_visibility(visibility)

    incident = Incident(
        title=title,
        description=description,
        service_name=service_name,
        severity=sev,
        status=IncidentStatus.INVESTIGATING,
        creator_id=creator_id,
        commander_id=commander_id or creator_id,
        visibility=vis,
        department=department.strip() if department else None,
        version=1,
    )
    db.add(incident)
    await db.flush()  # Get the incident ID without committing

    # Add creator as commander participant
    participant = IncidentParticipant(
        incident_id=incident.id,
        user_id=creator_id,
        role=ParticipantRole.COMMANDER,
    )
    db.add(participant)

    # Add creation event (atomic with the incident creation)
    _add_event(
        db, incident.id, creator_id, EventType.INCIDENT_CREATED,
        payload={
            "title": title,
            "service": service_name,
            "severity": sev.value,
            "visibility": vis.value,
            "department": incident.department,
        },
        event_version=1,
    )

    await db.commit()
    await db.refresh(incident)
    return incident


async def list_incidents(
    db: AsyncSession,
    user: User,
    status_filter: str | None = None,
    severity_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Incident], int]:
    # Enforce access control at database query level
    part_subquery = (
        select(IncidentParticipant.incident_id)
        .where(IncidentParticipant.user_id == user.id)
    )

    user_dept = (user.department or "").strip().lower()

    visibility_filter = or_(
        Incident.creator_id == user.id,
        Incident.commander_id == user.id,
        Incident.visibility == IncidentVisibility.ORGANIZATION,
        and_(
            Incident.visibility == IncidentVisibility.DEPARTMENT,
            Incident.department.isnot(None),
            func.lower(Incident.department) == user_dept,
        ),
        Incident.id.in_(part_subquery),
    )

    query = select(Incident).where(visibility_filter)
    count_query = select(func.count(Incident.id)).where(visibility_filter)

    if status_filter:
        st = _validate_status(status_filter)
        query = query.where(Incident.status == st)
        count_query = count_query.where(Incident.status == st)

    if severity_filter:
        sev = _validate_severity(severity_filter)
        query = query.where(Incident.severity == sev)
        count_query = count_query.where(Incident.severity == sev)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(Incident.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    incidents = list(result.scalars().all())
    return incidents, total


async def get_incident(db: AsyncSession, incident_id: UUID, user: User) -> Incident:
    incident = await _get_incident_or_404(db, incident_id)
    if not await can_view_incident(db, incident, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to view this incident",
        )
    return incident


async def update_incident_status(
    db: AsyncSession,
    incident_id: UUID,
    new_status: str,
    expected_version: int,
    user: User,
) -> Incident:
    incident = await _get_incident_or_404(db, incident_id)
    if not await can_modify_incident(db, incident, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only incident commanders and responders can modify this incident",
        )
    await _check_occ(incident, expected_version)

    new_st = _validate_status(new_status)
    old_st = incident.status

    if new_st not in VALID_STATUS_TRANSITIONS.get(old_st, []):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status transition from {old_st.value} to {new_st.value}",
        )

    incident.status = new_st
    incident.version += 1
    incident.updated_at = datetime.now(timezone.utc)

    _add_event(
        db, incident_id, user.id, EventType.STATUS_CHANGE,
        payload={"old_status": old_st.value, "new_status": new_st.value},
        event_version=incident.version,
    )

    await db.commit()
    await db.refresh(incident)
    return incident


async def update_incident_severity(
    db: AsyncSession,
    incident_id: UUID,
    new_severity: str,
    expected_version: int,
    user: User,
) -> Incident:
    incident = await _get_incident_or_404(db, incident_id)
    if not await can_modify_incident(db, incident, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only incident commanders and responders can modify this incident",
        )
    await _check_occ(incident, expected_version)

    new_sev = _validate_severity(new_severity)
    old_sev = incident.severity

    incident.severity = new_sev
    incident.version += 1
    incident.updated_at = datetime.now(timezone.utc)

    _add_event(
        db, incident_id, user.id, EventType.SEVERITY_CHANGE,
        payload={"old_severity": old_sev.value, "new_severity": new_sev.value},
        event_version=incident.version,
    )

    await db.commit()
    await db.refresh(incident)
    return incident


async def resolve_incident(
    db: AsyncSession,
    incident_id: UUID,
    expected_version: int,
    user: User,
    resolution_note: str | None = None,
) -> Incident:
    incident = await _get_incident_or_404(db, incident_id)
    if not await can_modify_incident(db, incident, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only incident commanders and responders can resolve this incident",
        )
    await _check_occ(incident, expected_version)

    if incident.status == IncidentStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Incident is already resolved",
        )

    old_status = incident.status
    incident.status = IncidentStatus.RESOLVED
    incident.version += 1
    incident.updated_at = datetime.now(timezone.utc)
    incident.resolved_at = datetime.now(timezone.utc)

    _add_event(
        db, incident_id, user.id, EventType.INCIDENT_RESOLVED,
        payload={"old_status": old_status.value, "resolution_note": resolution_note},
        event_version=incident.version,
    )

    await db.commit()
    await db.refresh(incident)
    return incident


# ---------------------------------------------------------------------------
# Participants
# ---------------------------------------------------------------------------

async def get_participants(db: AsyncSession, incident_id: UUID, user: User) -> list[IncidentParticipant]:
    incident = await _get_incident_or_404(db, incident_id)
    if not await can_view_incident(db, incident, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to view this incident",
        )

    result = await db.execute(
        select(IncidentParticipant)
        .where(IncidentParticipant.incident_id == incident_id)
        .order_by(IncidentParticipant.joined_at)
    )
    return list(result.scalars().all())


async def add_participant(
    db: AsyncSession,
    incident_id: UUID,
    user_id: UUID,
    role: str,
    actor: User,
) -> IncidentParticipant:
    incident = await _get_incident_or_404(db, incident_id)
    if not await can_modify_incident(db, incident, actor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only incident commanders and responders can invite or add participants",
        )

    _validate_role(role)

    # Check if user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    invited_user = user_result.scalar_one_or_none()
    if not invited_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if already a participant
    existing = await db.execute(
        select(IncidentParticipant).where(
            IncidentParticipant.incident_id == incident_id,
            IncidentParticipant.user_id == user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a participant")

    participant = IncidentParticipant(
        incident_id=incident_id,
        user_id=user_id,
        role=ParticipantRole(role),
    )
    db.add(participant)

    _add_event(
        db, incident_id, actor.id, EventType.PARTICIPANT_JOINED,
        payload={"user_id": str(user_id), "user_name": invited_user.name, "role": role},
    )

    await db.commit()
    await db.refresh(participant)
    return participant


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

async def post_message(
    db: AsyncSession,
    incident_id: UUID,
    user: User,
    body: str,
) -> IncidentMessage:
    incident = await _get_incident_or_404(db, incident_id)
    if not await can_view_incident(db, incident, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to access this incident",
        )

    message = IncidentMessage(
        incident_id=incident_id,
        author_id=user.id,
        body=body,
    )
    db.add(message)

    _add_event(
        db, incident_id, user.id, EventType.MESSAGE_POSTED,
        payload={"message_id": str(message.id), "body_preview": body[:200]},
    )

    await db.commit()
    await db.refresh(message)
    return message


async def list_messages(
    db: AsyncSession,
    incident_id: UUID,
    user: User,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[IncidentMessage], int]:
    incident = await _get_incident_or_404(db, incident_id)
    if not await can_view_incident(db, incident, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to view messages for this incident",
        )

    count_result = await db.execute(
        select(func.count(IncidentMessage.id)).where(IncidentMessage.incident_id == incident_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(IncidentMessage)
        .where(IncidentMessage.incident_id == incident_id)
        .order_by(IncidentMessage.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    messages = list(result.scalars().all())
    return messages, total


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

async def list_events(
    db: AsyncSession,
    incident_id: UUID,
    user: User,
    after_id: int | None = None,
    limit: int = 100,
) -> tuple[list[IncidentEvent], int]:
    incident = await _get_incident_or_404(db, incident_id)
    if not await can_view_incident(db, incident, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to view events for this incident",
        )

    query = select(IncidentEvent).where(IncidentEvent.incident_id == incident_id)
    count_query = select(func.count(IncidentEvent.id)).where(IncidentEvent.incident_id == incident_id)

    if after_id is not None:
        query = query.where(IncidentEvent.id > after_id)
        count_query = count_query.where(IncidentEvent.id > after_id)

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    result = await db.execute(query.order_by(IncidentEvent.id.asc()).limit(limit))
    events = list(result.scalars().all())
    return events, total
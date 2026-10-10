"""Incident management endpoints with visibility and role-based access control."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.db.session import get_db
from app.models.models import IncidentVisibility, User
from app.realtime.connection_manager import manager
from app.schemas.schemas import (
    EventListResponse,
    EventResponse,
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    MessageCreate,
    MessageListResponse,
    MessageResponse,
    ParticipantAdd,
    ParticipantResponse,
    ResolveRequest,
    SeverityUpdate,
    StatusUpdate,
)
from app.services import incident_service as svc
from app.services.auth_service import get_user_by_id

router = APIRouter(prefix="/incidents", tags=["Incidents"])


async def get_current_user_model(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def _enrich_incident(db, incident) -> IncidentResponse:
    """Attach creator/commander names to the response."""
    resp = IncidentResponse.model_validate(incident)
    creator = await get_user_by_id(db, incident.creator_id)
    if creator:
        resp.creator_name = creator.name
    if incident.commander_id:
        commander = await get_user_by_id(db, incident.commander_id)
        if commander:
            resp.commander_name = commander.name
    return resp


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.post("", response_model=IncidentResponse, status_code=201)
async def create_incident(
    data: IncidentCreate,
    user: User = Depends(get_current_user_model),
    db: AsyncSession = Depends(get_db),
):
    vis_val = data.visibility.value if hasattr(data.visibility, "value") else str(data.visibility)
    dept = data.department
    if str(vis_val).upper() == "DEPARTMENT" and not dept:
        dept = user.department

    incident = await svc.create_incident(
        db,
        title=data.title,
        description=data.description,
        service_name=data.service_name,
        severity=data.severity,
        creator_id=user.id,
        commander_id=data.commander_id,
        visibility=vis_val,
        department=dept,
    )
    return await _enrich_incident(db, incident)


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    status: str | None = Query(None),
    severity: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user_model),
    db: AsyncSession = Depends(get_db),
):
    incidents, total = await svc.list_incidents(db, user, status, severity, page, page_size)
    items = []
    for inc in incidents:
        items.append(await _enrich_incident(db, inc))
    return IncidentListResponse(incidents=items, total=total, page=page, page_size=page_size)


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    user: User = Depends(get_current_user_model),
    db: AsyncSession = Depends(get_db),
):
    incident = await svc.get_incident(db, incident_id, user)
    return await _enrich_incident(db, incident)


# ---------------------------------------------------------------------------
# Status / Severity / Resolve
# ---------------------------------------------------------------------------

@router.patch("/{incident_id}/status", response_model=IncidentResponse)
async def update_status(
    incident_id: UUID,
    data: StatusUpdate,
    user: User = Depends(get_current_user_model),
    db: AsyncSession = Depends(get_db),
):
    incident = await svc.update_incident_status(db, incident_id, data.status, data.version, user)
    resp = await _enrich_incident(db, incident)
    # Broadcast after commit
    await manager.broadcast_to_incident(incident_id, {
        "type": "status_change",
        "data": resp.model_dump(mode="json"),
    })
    return resp


@router.patch("/{incident_id}/severity", response_model=IncidentResponse)
async def update_severity(
    incident_id: UUID,
    data: SeverityUpdate,
    user: User = Depends(get_current_user_model),
    db: AsyncSession = Depends(get_db),
):
    incident = await svc.update_incident_severity(db, incident_id, data.severity, data.version, user)
    resp = await _enrich_incident(db, incident)
    await manager.broadcast_to_incident(incident_id, {
        "type": "severity_change",
        "data": resp.model_dump(mode="json"),
    })
    return resp


@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: UUID,
    data: ResolveRequest,
    user: User = Depends(get_current_user_model),
    db: AsyncSession = Depends(get_db),
):
    incident = await svc.resolve_incident(db, incident_id, data.version, user, data.resolution_note)
    resp = await _enrich_incident(db, incident)
    await manager.broadcast_to_incident(incident_id, {
        "type": "incident_resolved",
        "data": resp.model_dump(mode="json"),
    })
    return resp


# ---------------------------------------------------------------------------
# Participants
# ---------------------------------------------------------------------------

@router.get("/{incident_id}/participants", response_model=list[ParticipantResponse])
async def get_participants(
    incident_id: UUID,
    user: User = Depends(get_current_user_model),
    db: AsyncSession = Depends(get_db),
):
    participants = await svc.get_participants(db, incident_id, user)
    result = []
    for p in participants:
        resp = ParticipantResponse.model_validate(p)
        u = await get_user_by_id(db, p.user_id)
        if u:
            resp.user_name = u.name
            resp.user_email = u.email
        result.append(resp)
    return result


@router.post("/{incident_id}/participants", response_model=ParticipantResponse, status_code=201)
async def add_participant(
    incident_id: UUID,
    data: ParticipantAdd,
    user: User = Depends(get_current_user_model),
    db: AsyncSession = Depends(get_db),
):
    participant = await svc.add_participant(db, incident_id, data.user_id, data.role, user)
    resp = ParticipantResponse.model_validate(participant)
    invited_user = await get_user_by_id(db, data.user_id)
    if invited_user:
        resp.user_name = invited_user.name
        resp.user_email = invited_user.email
    await manager.broadcast_to_incident(incident_id, {
        "type": "participant_joined",
        "data": resp.model_dump(mode="json"),
    })
    return resp


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

@router.post("/{incident_id}/messages", response_model=MessageResponse, status_code=201)
async def post_message(
    incident_id: UUID,
    data: MessageCreate,
    user: User = Depends(get_current_user_model),
    db: AsyncSession = Depends(get_db),
):
    message = await svc.post_message(db, incident_id, user, data.body)
    resp = MessageResponse.model_validate(message)
    resp.author_name = user.name
    await manager.broadcast_to_incident(incident_id, {
        "type": "new_message",
        "data": resp.model_dump(mode="json"),
    })
    return resp


@router.get("/{incident_id}/messages", response_model=MessageListResponse)
async def list_messages(
    incident_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user_model),
    db: AsyncSession = Depends(get_db),
):
    messages, total = await svc.list_messages(db, incident_id, user, page, page_size)
    items = []
    for m in messages:
        resp = MessageResponse.model_validate(m)
        author = await get_user_by_id(db, m.author_id)
        if author:
            resp.author_name = author.name
        items.append(resp)
    return MessageListResponse(messages=items, total=total)


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

@router.get("/{incident_id}/events", response_model=EventListResponse)
async def list_events(
    incident_id: UUID,
    after_id: int | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user_model),
    db: AsyncSession = Depends(get_db),
):
    events, total = await svc.list_events(db, incident_id, user, after_id, limit)
    items = []
    for e in events:
        resp = EventResponse.model_validate(e)
        if e.actor_id:
            actor = await get_user_by_id(db, e.actor_id)
            if actor:
                resp.actor_name = actor.name
        items.append(resp)
    return EventListResponse(events=items, total=total)
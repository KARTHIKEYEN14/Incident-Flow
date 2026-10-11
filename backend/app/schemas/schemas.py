"""Pydantic request/response schemas."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    created_at: Optional[datetime] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    email: str
    created_at: datetime
    department: Optional[str] = 'Engineering'
    department_id: Optional[UUID] = None


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=6)
    department_id: UUID


# ---------------------------------------------------------------------------
# Incident
# ---------------------------------------------------------------------------

class IncidentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = None
    service_name: str = Field(min_length=1, max_length=255)
    severity: str = Field(default="SEV-3")
    commander_id: Optional[UUID] = None
    visibility: str = Field(default='ORGANIZATION')
    department: Optional[str] = None


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    description: Optional[str]
    service_name: str
    severity: str
    status: str
    commander_id: Optional[UUID]
    creator_id: UUID
    version: int
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    creator_name: Optional[str] = None
    commander_name: Optional[str] = None
    visibility: str = 'ORGANIZATION'
    department: Optional[str] = None


class IncidentListResponse(BaseModel):
    incidents: list[IncidentResponse]
    total: int
    page: int
    page_size: int


class StatusUpdate(BaseModel):
    status: str
    version: int  # Client must supply current version for OCC


class SeverityUpdate(BaseModel):
    severity: str
    version: int


class ResolveRequest(BaseModel):
    version: int
    resolution_note: Optional[str] = None


# ---------------------------------------------------------------------------
# Participants
# ---------------------------------------------------------------------------

class ParticipantAdd(BaseModel):
    user_id: UUID
    role: str = "RESPONDER"


class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    incident_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime
    user_name: Optional[str] = None
    user_email: Optional[str] = None


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    incident_id: UUID
    author_id: UUID
    body: str
    created_at: datetime
    author_name: Optional[str] = None


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    total: int


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    incident_id: UUID
    actor_id: Optional[UUID]
    event_type: str
    payload: Optional[dict[str, Any]]
    event_version: Optional[int]
    created_at: datetime
    actor_name: Optional[str] = None


class EventListResponse(BaseModel):
    events: list[EventResponse]
    total: int


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

class WSMessage(BaseModel):
    type: str
    data: dict[str, Any] = {}

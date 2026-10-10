"""SQLAlchemy ORM models for the Incident War Room."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SeverityLevel(str, enum.Enum):
    SEV1 = "SEV-1"
    SEV2 = "SEV-2"
    SEV3 = "SEV-3"
    SEV4 = "SEV-4"


class IncidentStatus(str, enum.Enum):
    INVESTIGATING = "INVESTIGATING"
    IDENTIFIED = "IDENTIFIED"
    MONITORING = "MONITORING"
    RESOLVED = "RESOLVED"


class IncidentVisibility(str, enum.Enum):
    ORGANIZATION = 'ORGANIZATION'
    DEPARTMENT = 'DEPARTMENT'
    RESTRICTED = 'RESTRICTED'


class ParticipantRole(str, enum.Enum):
    COMMANDER = "COMMANDER"
    RESPONDER = "RESPONDER"
    OBSERVER = "OBSERVER"


class EventType(str, enum.Enum):
    INCIDENT_CREATED = "INCIDENT_CREATED"
    STATUS_CHANGE = "STATUS_CHANGE"
    SEVERITY_CHANGE = "SEVERITY_CHANGE"
    MESSAGE_POSTED = "MESSAGE_POSTED"
    PARTICIPANT_JOINED = "PARTICIPANT_JOINED"
    PARTICIPANT_LEFT = "PARTICIPANT_LEFT"
    INCIDENT_RESOLVED = "INCIDENT_RESOLVED"


# ---------------------------------------------------------------------------
# Valid status transitions
# ---------------------------------------------------------------------------

VALID_STATUS_TRANSITIONS: dict[IncidentStatus, list[IncidentStatus]] = {
    IncidentStatus.INVESTIGATING: [IncidentStatus.IDENTIFIED, IncidentStatus.MONITORING, IncidentStatus.RESOLVED],
    IncidentStatus.IDENTIFIED: [IncidentStatus.MONITORING, IncidentStatus.RESOLVED],
    IncidentStatus.MONITORING: [IncidentStatus.RESOLVED, IncidentStatus.INVESTIGATING],
    IncidentStatus.RESOLVED: [IncidentStatus.INVESTIGATING],
}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(320), nullable=False, unique=True, index=True)
    password_hash = Column(String(512), nullable=False)
    department = Column(String(100), nullable=False, default='Engineering')
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    created_incidents = relationship("Incident", back_populates="creator", foreign_keys="Incident.creator_id")
    commanded_incidents = relationship("Incident", back_populates="commander", foreign_keys="Incident.commander_id")
    participations = relationship("IncidentParticipant", back_populates="user")
    messages = relationship("IncidentMessage", back_populates="author")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    service_name = Column(String(255), nullable=False)
    visibility = Column(Enum(IncidentVisibility, name='incident_visibility', values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=IncidentVisibility.ORGANIZATION)
    department = Column(String(100), nullable=True)
    severity = Column(Enum(SeverityLevel, name="severity_level", values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=SeverityLevel.SEV3)
    status = Column(Enum(IncidentStatus, name="incident_status", values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=IncidentStatus.INVESTIGATING)
    commander_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    creator = relationship("User", back_populates="created_incidents", foreign_keys=[creator_id])
    commander = relationship("User", back_populates="commanded_incidents", foreign_keys=[commander_id])
    participants = relationship("IncidentParticipant", back_populates="incident", cascade="all, delete-orphan")
    events = relationship("IncidentEvent", back_populates="incident", cascade="all, delete-orphan", order_by="IncidentEvent.id")
    messages = relationship("IncidentMessage", back_populates="incident", cascade="all, delete-orphan", order_by="IncidentMessage.created_at")

    __table_args__ = (
        Index("ix_incidents_status", "status"),
        Index("ix_incidents_severity", "severity"),
        Index("ix_incidents_created_at", "created_at"),
    )


class IncidentParticipant(Base):
    __tablename__ = "incident_participants"

    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role = Column(Enum(ParticipantRole, name="participant_role", values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=ParticipantRole.RESPONDER)
    joined_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    incident = relationship("Incident", back_populates="participants")
    user = relationship("User", back_populates="participations")

    __table_args__ = (
        UniqueConstraint("incident_id", "user_id", name="uq_incident_participant"),
    )


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id = Column(Integer, primary_key=True, autoincrement=True)  # DB-generated, deterministic ordering
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type = Column(Enum(EventType, name="event_type", values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    payload = Column(JSONB, nullable=True)
    event_version = Column(Integer, nullable=True)  # Incident version at event time
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    incident = relationship("Incident", back_populates="events")
    actor = relationship("User")

    __table_args__ = (
        Index("ix_incident_events_incident_id", "incident_id"),
        Index("ix_incident_events_created_at", "created_at"),
    )


class IncidentMessage(Base):
    __tablename__ = "incident_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    incident = relationship("Incident", back_populates="messages")
    author = relationship("User", back_populates="messages")

    __table_args__ = (
        Index("ix_incident_messages_incident_id", "incident_id"),
        Index("ix_incident_messages_created_at", "created_at"),
    )

"""Initial schema migration — pure SQL approach to avoid SQLAlchemy Enum auto-create.

Revision ID: 001_initial
Revises:
Create Date: 2026-10-10
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE severity_level AS ENUM ('SEV-1', 'SEV-2', 'SEV-3', 'SEV-4');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE incident_status AS ENUM ('INVESTIGATING', 'IDENTIFIED', 'MONITORING', 'RESOLVED');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE participant_role AS ENUM ('COMMANDER', 'RESPONDER', 'OBSERVER');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE event_type AS ENUM (
                'INCIDENT_CREATED', 'STATUS_CHANGE', 'SEVERITY_CHANGE',
                'MESSAGE_POSTED', 'PARTICIPANT_JOINED', 'PARTICIPANT_LEFT', 'INCIDENT_RESOLVED'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(320) NOT NULL UNIQUE,
            password_hash VARCHAR(512) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

        CREATE TABLE IF NOT EXISTS incidents (
            id UUID PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            description TEXT,
            service_name VARCHAR(255) NOT NULL,
            severity severity_level NOT NULL,
            status incident_status NOT NULL,
            commander_id UUID REFERENCES users(id),
            creator_id UUID NOT NULL REFERENCES users(id),
            version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            resolved_at TIMESTAMPTZ
        );
        CREATE INDEX IF NOT EXISTS ix_incidents_status ON incidents (status);
        CREATE INDEX IF NOT EXISTS ix_incidents_severity ON incidents (severity);
        CREATE INDEX IF NOT EXISTS ix_incidents_created_at ON incidents (created_at);

        CREATE TABLE IF NOT EXISTS incident_participants (
            incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id),
            role participant_role NOT NULL,
            joined_at TIMESTAMPTZ NOT NULL,
            PRIMARY KEY (incident_id, user_id),
            CONSTRAINT uq_incident_participant UNIQUE (incident_id, user_id)
        );

        CREATE SEQUENCE IF NOT EXISTS incident_events_id_seq;
        CREATE TABLE IF NOT EXISTS incident_events (
            id INTEGER PRIMARY KEY DEFAULT nextval('incident_events_id_seq'),
            incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
            actor_id UUID REFERENCES users(id),
            event_type event_type NOT NULL,
            payload JSONB,
            event_version INTEGER,
            created_at TIMESTAMPTZ NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_incident_events_incident_id ON incident_events (incident_id);
        CREATE INDEX IF NOT EXISTS ix_incident_events_created_at ON incident_events (created_at);

        CREATE TABLE IF NOT EXISTS incident_messages (
            id UUID PRIMARY KEY,
            incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
            author_id UUID NOT NULL REFERENCES users(id),
            body TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_incident_messages_incident_id ON incident_messages (incident_id);
        CREATE INDEX IF NOT EXISTS ix_incident_messages_created_at ON incident_messages (created_at);
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        DROP TABLE IF EXISTS incident_messages;
        DROP TABLE IF EXISTS incident_events;
        DROP SEQUENCE IF EXISTS incident_events_id_seq;
        DROP TABLE IF EXISTS incident_participants;
        DROP TABLE IF EXISTS incidents;
        DROP TABLE IF EXISTS users;
        DROP TYPE IF EXISTS event_type;
        DROP TYPE IF EXISTS participant_role;
        DROP TYPE IF EXISTS incident_status;
        DROP TYPE IF EXISTS severity_level;
    """))

"""Add incident visibility and user department.

Revision ID: 002_incident_visibility
Revises: 001_initial
Create Date: 2026-10-10
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_incident_visibility'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE incident_visibility AS ENUM ('ORGANIZATION', 'DEPARTMENT', 'RESTRICTED');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(100) NOT NULL DEFAULT 'Engineering';

        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS visibility incident_visibility NOT NULL DEFAULT 'ORGANIZATION';
        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS department VARCHAR(100) NULL;

        CREATE INDEX IF NOT EXISTS ix_incidents_visibility ON incidents (visibility);
        CREATE INDEX IF NOT EXISTS ix_incidents_department ON incidents (department);
        CREATE INDEX IF NOT EXISTS ix_users_department ON users (department);
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        DROP INDEX IF EXISTS ix_users_department;
        DROP INDEX IF EXISTS ix_incidents_department;
        DROP INDEX IF EXISTS ix_incidents_visibility;
        ALTER TABLE incidents DROP COLUMN IF EXISTS department;
        ALTER TABLE incidents DROP COLUMN IF EXISTS visibility;
        ALTER TABLE users DROP COLUMN IF EXISTS department;
        DROP TYPE IF EXISTS incident_visibility;
    """))

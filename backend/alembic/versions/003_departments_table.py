"""Add departments table, user department_id foreign key, and seed departments.

Revision ID: 003_departments_table
Revises: 002_incident_visibility
Create Date: 2026-10-10
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_departments_table'
down_revision: Union[str, None] = '002_incident_visibility'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS departments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS ix_departments_name ON departments (name);

        ALTER TABLE users ADD COLUMN IF NOT EXISTS department_id UUID NULL;

        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_users_department_id'
            ) THEN
                ALTER TABLE users 
                ADD CONSTRAINT fk_users_department_id 
                FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL;
            END IF;
        END $$;

        CREATE INDEX IF NOT EXISTS ix_users_department_id ON users (department_id);

        INSERT INTO departments (name)
        VALUES 
            ('IT'),
            ('HR'),
            ('Finance'),
            ('Operations'),
            ('Security'),
            ('Marketing'),
            ('Engineering')
        ON CONFLICT (name) DO NOTHING;

        UPDATE users u
        SET department_id = d.id
        FROM departments d
        WHERE LOWER(u.department) = LOWER(d.name) AND u.department_id IS NULL;

        UPDATE users u
        SET department_id = (SELECT id FROM departments WHERE name = 'Engineering' LIMIT 1),
            department = 'Engineering'
        WHERE u.department_id IS NULL;
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        DROP INDEX IF EXISTS ix_users_department_id;
        ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_department_id;
        ALTER TABLE users DROP COLUMN IF EXISTS department_id;
        DROP INDEX IF EXISTS ix_departments_name;
        DROP TABLE IF EXISTS departments;
    """))

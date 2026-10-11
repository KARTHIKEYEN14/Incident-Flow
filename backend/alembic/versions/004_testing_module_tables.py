"""Add automated testing module tables: runs, cases, results, and feature snapshots.

Revision ID: 004_testing_module_tables
Revises: 003_departments_table
Create Date: 2026-10-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_testing_module_tables'
down_revision: Union[str, None] = '003_departments_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS testing_feature_snapshots (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            discovered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            generator_version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
            feature_count INTEGER NOT NULL DEFAULT 0,
            features JSONB NOT NULL
        );

        CREATE INDEX IF NOT EXISTS ix_testing_feature_snapshots_discovered_at 
            ON testing_feature_snapshots (discovered_at);

        CREATE TABLE IF NOT EXISTS testing_test_cases (
            id VARCHAR(100) PRIMARY KEY,
            test_key VARCHAR(100) NOT NULL UNIQUE,
            feature_name VARCHAR(150) NOT NULL,
            category VARCHAR(50) NOT NULL,
            title VARCHAR(300) NOT NULL,
            description TEXT NULL,
            source_evidence JSONB NOT NULL,
            preconditions JSONB NULL,
            test_steps JSONB NOT NULL,
            input_data JSONB NULL,
            expected_outcome JSONB NOT NULL,
            generator_version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS ix_testing_test_cases_test_key 
            ON testing_test_cases (test_key);
        CREATE INDEX IF NOT EXISTS ix_testing_test_cases_feature_name 
            ON testing_test_cases (feature_name);
        CREATE INDEX IF NOT EXISTS ix_testing_test_cases_category 
            ON testing_test_cases (category);

        CREATE TABLE IF NOT EXISTS testing_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            started_at TIMESTAMPTZ NULL,
            completed_at TIMESTAMPTZ NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
            generator_version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
            triggered_by VARCHAR(255) NULL,
            total_tests INTEGER NOT NULL DEFAULT 0,
            passed_tests INTEGER NOT NULL DEFAULT 0,
            failed_tests INTEGER NOT NULL DEFAULT 0,
            blocked_tests INTEGER NOT NULL DEFAULT 0,
            skipped_tests INTEGER NOT NULL DEFAULT 0,
            duration_ms DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            environment_info JSONB NULL,
            summary_notes TEXT NULL
        );

        CREATE INDEX IF NOT EXISTS ix_testing_runs_created_at 
            ON testing_runs (created_at);
        CREATE INDEX IF NOT EXISTS ix_testing_runs_status 
            ON testing_runs (status);

        CREATE TABLE IF NOT EXISTS testing_results (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            run_id UUID NOT NULL REFERENCES testing_runs(id) ON DELETE CASCADE,
            test_case_id VARCHAR(100) NOT NULL REFERENCES testing_test_cases(id) ON DELETE CASCADE,
            feature_name VARCHAR(150) NOT NULL,
            category VARCHAR(50) NOT NULL,
            title VARCHAR(300) NOT NULL,
            status VARCHAR(50) NOT NULL,
            duration_ms DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            expected_outcome JSONB NOT NULL,
            actual_outcome JSONB NOT NULL,
            error_message TEXT NULL,
            error_details JSONB NULL,
            executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS ix_testing_results_run_id 
            ON testing_results (run_id);
        CREATE INDEX IF NOT EXISTS ix_testing_results_test_case_id 
            ON testing_results (test_case_id);
        CREATE INDEX IF NOT EXISTS ix_testing_results_feature_name 
            ON testing_results (feature_name);
        CREATE INDEX IF NOT EXISTS ix_testing_results_status 
            ON testing_results (status);
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        DROP TABLE IF EXISTS testing_results CASCADE;
        DROP TABLE IF EXISTS testing_runs CASCADE;
        DROP TABLE IF EXISTS testing_test_cases CASCADE;
        DROP TABLE IF EXISTS testing_feature_snapshots CASCADE;
    """))

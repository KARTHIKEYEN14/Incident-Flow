"""SQLAlchemy ORM models for the Automated Testing Module."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class TestCategory(str, enum.Enum):
    FUNCTIONAL = "FUNCTIONAL"
    VALIDATION = "VALIDATION"
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    BOUNDARY = "BOUNDARY"
    CONCURRENCY = "CONCURRENCY"
    DATABASE_INTEGRITY = "DATABASE_INTEGRITY"
    REALTIME = "REALTIME"
    REGRESSION = "REGRESSION"


class TestStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class RunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class FeatureSnapshot(Base):
    __tablename__ = "testing_feature_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    discovered_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    generator_version = Column(String(50), nullable=False, default="1.0.0")
    feature_count = Column(Integer, nullable=False, default=0)
    features = Column(JSONB, nullable=False)  # List of discovered features with verified contracts

    __table_args__ = (
        Index("ix_testing_feature_snapshots_discovered_at", "discovered_at"),
    )


class TestCaseRecord(Base):
    __tablename__ = "testing_test_cases"

    id = Column(String(100), primary_key=True)  # e.g., TC-AUTH-001
    test_key = Column(String(100), nullable=False, unique=True, index=True)
    feature_name = Column(String(150), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    source_evidence = Column(JSONB, nullable=False)  # endpoints, schemas, validation rules
    preconditions = Column(JSONB, nullable=True)
    test_steps = Column(JSONB, nullable=False)
    input_data = Column(JSONB, nullable=True)
    expected_outcome = Column(JSONB, nullable=False)
    generator_version = Column(String(50), nullable=False, default="1.0.0")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    results = relationship("TestCaseResultRecord", back_populates="test_case", cascade="all, delete-orphan")


class TestRunRecord(Base):
    __tablename__ = "testing_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default=RunStatus.PENDING.value)
    generator_version = Column(String(50), nullable=False, default="1.0.0")
    triggered_by = Column(String(255), nullable=True)
    total_tests = Column(Integer, nullable=False, default=0)
    passed_tests = Column(Integer, nullable=False, default=0)
    failed_tests = Column(Integer, nullable=False, default=0)
    blocked_tests = Column(Integer, nullable=False, default=0)
    skipped_tests = Column(Integer, nullable=False, default=0)
    duration_ms = Column(Float, nullable=False, default=0.0)
    environment_info = Column(JSONB, nullable=True)
    summary_notes = Column(Text, nullable=True)

    results = relationship("TestCaseResultRecord", back_populates="test_run", cascade="all, delete-orphan", order_by="TestCaseResultRecord.executed_at")

    __table_args__ = (
        Index("ix_testing_runs_created_at", "created_at"),
        Index("ix_testing_runs_status", "status"),
    )


class TestCaseResultRecord(Base):
    __tablename__ = "testing_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("testing_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    test_case_id = Column(String(100), ForeignKey("testing_test_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    feature_name = Column(String(150), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    status = Column(String(50), nullable=False, index=True)  # PASSED, FAILED, BLOCKED, SKIPPED
    duration_ms = Column(Float, nullable=False, default=0.0)
    expected_outcome = Column(JSONB, nullable=False)
    actual_outcome = Column(JSONB, nullable=False)
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    test_run = relationship("TestRunRecord", back_populates="results")
    test_case = relationship("TestCaseRecord", back_populates="results")


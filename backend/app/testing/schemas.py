"""Pydantic schemas for the Automated Testing Module."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EndpointEvidence(BaseModel):
    method: str
    path: str
    summary: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    auth_required: bool = False
    status_codes: list[int] = Field(default_factory=list)


class DiscoveredFeature(BaseModel):
    id: str
    name: str
    category: str
    description: str
    implemented: bool = True
    evidence_type: str = "CODE_AND_SCHEMA"
    endpoints: list[EndpointEvidence] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)
    rules_and_constraints: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class FeatureInventory(BaseModel):
    discovery_timestamp: datetime
    generator_version: str = "1.0.0"
    engine: str = "AST + FastAPI Route & SQLAlchemy Model Introspection"
    total_features: int
    features: list[DiscoveredFeature]
    excluded_features: list[dict[str, str]] = Field(default_factory=list)


class TestCaseDefinition(BaseModel):
    id: str  # e.g., TC-AUTH-001
    test_key: str
    feature_name: str
    category: str  # FUNCTIONAL, VALIDATION, AUTHENTICATION, AUTHORIZATION, BOUNDARY, CONCURRENCY, DATABASE_INTEGRITY, REALTIME
    title: str
    description: Optional[str] = None
    source_evidence: dict[str, Any]
    preconditions: Optional[list[str]] = Field(default_factory=list)
    test_steps: list[str]
    input_data: Optional[dict[str, Any]] = None
    expected_outcome: dict[str, Any]  # e.g., status_code, fields, occ_conflict, error_detail
    generator_version: str = "1.0.0"
    validation_status: str = "VALIDATED"


class TestCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    test_key: str
    feature_name: str
    category: str
    title: str
    description: Optional[str] = None
    source_evidence: dict[str, Any]
    preconditions: Optional[Any] = None
    test_steps: list[str]
    input_data: Optional[dict[str, Any]] = None
    expected_outcome: dict[str, Any]
    generator_version: str


class TestCaseResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    run_id: UUID
    test_case_id: str
    feature_name: str
    category: str
    title: str
    status: str  # PASSED, FAILED, BLOCKED, SKIPPED
    duration_ms: float
    expected_outcome: dict[str, Any]
    actual_outcome: dict[str, Any]
    error_message: Optional[str] = None
    error_details: Optional[dict[str, Any]] = None
    executed_at: datetime


class TestRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str
    generator_version: str
    triggered_by: Optional[str] = None
    total_tests: int
    passed_tests: int
    failed_tests: int
    blocked_tests: int
    skipped_tests: int
    duration_ms: float
    pass_percentage: float = 0.0
    summary_notes: Optional[str] = None


class TestRunDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    run: TestRunSummary
    results: list[TestCaseResultResponse]
    results_by_feature: dict[str, list[TestCaseResultResponse]] = Field(default_factory=dict)
    feature_summaries: list[dict[str, Any]] = Field(default_factory=list)


class RunTestsRequest(BaseModel):
    test_case_ids: Optional[list[str]] = None  # None means run all approved tests
    feature_filter: Optional[str] = None

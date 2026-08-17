"""Domain data classes — Mission 001-006 consolidated."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from typing import Optional

from .enums import (
    RunLifecycle, GateStatus, MasterJobStatus, ConnectionStatus,
    StageType, StageStatus, StageApplicability, StageCriticality,
    FindingSeverity, ErrorClassification,
)


@dataclass
class Project:
    id: str = field(default_factory=lambda: uuid4().hex)
    org_id: str = ""
    name: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VerificationRun:
    id: str = field(default_factory=lambda: uuid4().hex)
    project_id: str = ""
    lifecycle: RunLifecycle = RunLifecycle.CREATED
    commit_hash: str = ""
    branch: str = ""
    error_classification: Optional[ErrorClassification] = None
    error_detail: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class MasterVerificationJob:
    id: str = field(default_factory=lambda: uuid4().hex)
    project_id: str = ""
    status: MasterJobStatus = MasterJobStatus.CREATED
    repo_url: str = ""
    branch: str = ""
    commit_hash: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class VerificationStage:
    id: str = field(default_factory=lambda: uuid4().hex)
    master_job_id: str = ""
    stage_type: StageType = StageType.INTAKE
    status: StageStatus = StageStatus.PENDING
    applicability: StageApplicability = StageApplicability.REQUIRED
    criticality: StageCriticality = StageCriticality.REQUIRED
    seq: int = 0
    output: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class RepositoryConnection:
    id: str = field(default_factory=lambda: uuid4().hex)
    project_id: str = ""
    url: str = ""
    status: ConnectionStatus = ConnectionStatus.SUBMITTED
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VerificationGate:
    id: str = field(default_factory=lambda: uuid4().hex)
    run_id: str = ""
    name: str = ""
    status: GateStatus = GateStatus.PLANNED
    description: str = ""
    passed: bool = False
    evidence_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Finding:
    id: str = field(default_factory=lambda: uuid4().hex)
    run_id: str = ""
    severity: FindingSeverity = FindingSeverity.MEDIUM
    title: str = ""
    description: str = ""
    location: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Recommendation:
    id: str = field(default_factory=lambda: uuid4().hex)
    run_id: str = ""
    finding_id: str = ""
    title: str = ""
    description: str = ""
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Approval:
    id: str = field(default_factory=lambda: uuid4().hex)
    run_id: str = ""
    scope: str = ""
    granted: bool = False
    granted_by: str = ""
    reason: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EvidenceItem:
    id: str = field(default_factory=lambda: uuid4().hex)
    run_id: str = ""
    type: str = ""
    content: str = ""
    source: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditEvent:
    id: str = field(default_factory=lambda: uuid4().hex)
    run_id: str = ""
    event_type: str = ""
    detail: str = ""
    actor: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

"""Plan domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from typing import Optional

from .plan_enums import PlanStatus, CommandSource, CommandConfidence, CommandExecutionStatus, Ecosystem


@dataclass
class VerificationPlan:
    id: str = field(default_factory=lambda: uuid4().hex)
    master_job_id: str = ""
    ecosystem: Ecosystem = Ecosystem.UNKNOWN
    status: PlanStatus = PlanStatus.DRAFT
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PlanStage:
    id: str = field(default_factory=lambda: uuid4().hex)
    plan_id: str = ""
    name: str = ""
    seq: int = 0
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CommandSpecification:
    id: str = field(default_factory=lambda: uuid4().hex)
    plan_stage_id: str = ""
    command: str = ""
    source: CommandSource = CommandSource.DETERMINISTIC
    confidence: CommandConfidence = CommandConfidence.MEDIUM
    execution_status: CommandExecutionStatus = CommandExecutionStatus.PENDING
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PlanConflict:
    id: str = field(default_factory=lambda: uuid4().hex)
    plan_id: str = ""
    description: str = ""
    resolution: Optional[str] = None
    resolved: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PlanDigest:
    plan_id: str = ""
    ecosystem: Ecosystem = Ecosystem.UNKNOWN
    stage_count: int = 0
    command_count: int = 0
    conflicts: int = 0
    checksum: str = ""

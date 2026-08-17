"""Policy domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from typing import Optional

from .policy_enums import (
    PolicyDecision, PolicyOutcome, RiskLevel,
    RestrictionType, ApprovalScope, PolicyArea
)


@dataclass
class PolicyEvaluation:
    id: str = field(default_factory=lambda: uuid4().hex)
    master_job_id: str = ""
    overall_decision: PolicyDecision = PolicyDecision.ALLOW
    risk_level: RiskLevel = RiskLevel.NONE
    requires_approval: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PolicyValidationResult:
    id: str = field(default_factory=lambda: uuid4().hex)
    evaluation_id: str = ""
    rule_id: str = ""
    rule_name: str = ""
    area: PolicyArea = PolicyArea.SECURITY
    outcome: PolicyOutcome = PolicyOutcome.PASS
    decision: PolicyDecision = PolicyDecision.ALLOW
    message: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PolicyRule:
    id: str = field(default_factory=lambda: uuid4().hex)
    name: str = ""
    area: PolicyArea = PolicyArea.SECURITY
    description: str = ""
    risk_level: RiskLevel = RiskLevel.MEDIUM
    enabled: bool = True
    config: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PolicyRestriction:
    id: str = field(default_factory=lambda: uuid4().hex)
    result_id: str = ""
    restriction_type: RestrictionType = RestrictionType.NETWORK
    description: str = ""
    value: str = ""
    scope: ApprovalScope = ApprovalScope.SINGLE_RUN
    created_at: datetime = field(default_factory=datetime.utcnow)

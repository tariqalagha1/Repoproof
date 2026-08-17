"""Policy domain enums."""

from enum import Enum


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"
    REQUIRE_APPROVAL = "require_approval"
    NOT_APPLICABLE = "not_applicable"


class PolicyOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    ERROR = "error"
    SKIPPED = "skipped"


class RiskLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RestrictionType(str, Enum):
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    CAPABILITY = "capability"
    RESOURCE = "resource"
    TIMEOUT = "timeout"
    EXECUTION = "execution"


class ApprovalScope(str, Enum):
    SINGLE_RUN = "single_run"
    MASTER_JOB = "master_job"
    PROJECT = "project"
    GLOBAL = "global"


class PolicyArea(str, Enum):
    SECURITY = "security"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"
    QUALITY = "quality"
    ARCHITECTURE = "architecture"

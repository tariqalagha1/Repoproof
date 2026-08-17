"""Domain enums — Mission 001-006 consolidated."""

from enum import Enum


class RunLifecycle(str, Enum):
    CREATED = "created"
    DISCOVERING = "discovering"
    PLAN_READY = "plan_ready"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    PROVISIONING = "provisioning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    REPORTING = "reporting"
    COMPLETED = "completed"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


ALLOWED_TRANSITIONS: dict[RunLifecycle, set[RunLifecycle]] = {
    RunLifecycle.CREATED: {RunLifecycle.DISCOVERING, RunLifecycle.CANCELLED},
    RunLifecycle.DISCOVERING: {RunLifecycle.PLAN_READY, RunLifecycle.FAILED, RunLifecycle.BLOCKED, RunLifecycle.CANCELLED},
    RunLifecycle.PLAN_READY: {RunLifecycle.AWAITING_APPROVAL, RunLifecycle.FAILED, RunLifecycle.BLOCKED, RunLifecycle.CANCELLED},
    RunLifecycle.AWAITING_APPROVAL: {RunLifecycle.APPROVED, RunLifecycle.FAILED, RunLifecycle.CANCELLED},
    RunLifecycle.APPROVED: {RunLifecycle.PROVISIONING, RunLifecycle.FAILED, RunLifecycle.CANCELLED},
    RunLifecycle.PROVISIONING: {RunLifecycle.EXECUTING, RunLifecycle.FAILED, RunLifecycle.BLOCKED, RunLifecycle.CANCELLED},
    RunLifecycle.EXECUTING: {RunLifecycle.VERIFYING, RunLifecycle.FAILED, RunLifecycle.BLOCKED, RunLifecycle.CANCELLED},
    RunLifecycle.VERIFYING: {RunLifecycle.REPORTING, RunLifecycle.FAILED, RunLifecycle.BLOCKED, RunLifecycle.CANCELLED},
    RunLifecycle.REPORTING: {RunLifecycle.COMPLETED, RunLifecycle.FAILED, RunLifecycle.BLOCKED, RunLifecycle.CANCELLED},
    RunLifecycle.COMPLETED: set(),
    RunLifecycle.FAILED: {RunLifecycle.DISCOVERING, RunLifecycle.CANCELLED},
    RunLifecycle.BLOCKED: {RunLifecycle.DISCOVERING, RunLifecycle.FAILED, RunLifecycle.CANCELLED},
    RunLifecycle.PARTIAL: {RunLifecycle.DISCOVERING, RunLifecycle.COMPLETED, RunLifecycle.FAILED, RunLifecycle.CANCELLED},
    RunLifecycle.CANCELLED: set(),
}


class GateStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class MasterJobStatus(str, Enum):
    CREATED = "created"
    INTAKE_PENDING = "intake_pending"
    DISCOVERING = "discovering"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    COMPLETED_WITH_FINDINGS = "completed_with_findings"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class ConnectionStatus(str, Enum):
    SUBMITTED = "submitted"
    VALID = "valid"
    INVALID = "invalid"
    DISCOVERED = "discovered"
    ERROR = "error"


class StageType(str, Enum):
    INTAKE = "00_intake"
    PASSIVE_DISCOVERY = "01_passive_discovery"
    PLAN_GENERATION = "02_plan_generation"
    POLICY_VALIDATION = "03_policy_validation"
    ENVIRONMENT_PROVISIONING = "04_environment_provisioning"
    DEPENDENCY_INSTALLATION = "05_dependency_installation"
    PRE_RUNTIME_VERIFICATION = "06_pre_runtime_verification"
    BUILD = "07_build"
    INFRASTRUCTURE_STARTUP = "08_infrastructure_startup"
    APPLICATION_STARTUP = "09_application_startup"
    LIVE_WORKFLOW_TESTING = "10_live_workflow_testing"
    ARCHITECTURE_PORTABILITY = "11_architecture_portability"
    PRODUCTION_READINESS = "12_production_readiness"
    OUTPUT_CORRECTNESS = "13_output_correctness"
    COMPLIANCE = "14_compliance"
    FINAL_ADVISORY_REPORT = "15_final_advisory_report"


class StageStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_FINDINGS = "completed_with_findings"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED_NOT_APPLICABLE = "skipped_not_applicable"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StageApplicability(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    CONDITIONAL = "conditional"


class StageCriticality(str, Enum):
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


STAGE_DEFINITIONS = [
    {"type": StageType.INTAKE, "seq": 0, "name": "Intake", "criticality": StageCriticality.REQUIRED, "applicability": StageApplicability.REQUIRED},
    {"type": StageType.PASSIVE_DISCOVERY, "seq": 1, "name": "Passive Discovery", "criticality": StageCriticality.REQUIRED, "applicability": StageApplicability.REQUIRED},
    {"type": StageType.PLAN_GENERATION, "seq": 2, "name": "Plan Generation", "criticality": StageCriticality.REQUIRED, "applicability": StageApplicability.REQUIRED},
    {"type": StageType.POLICY_VALIDATION, "seq": 3, "name": "Policy Validation", "criticality": StageCriticality.REQUIRED, "applicability": StageApplicability.REQUIRED},
    {"type": StageType.ENVIRONMENT_PROVISIONING, "seq": 4, "name": "Environment Provisioning", "criticality": StageCriticality.REQUIRED, "applicability": StageApplicability.REQUIRED},
    {"type": StageType.DEPENDENCY_INSTALLATION, "seq": 5, "name": "Dependency Installation", "criticality": StageCriticality.REQUIRED, "applicability": StageApplicability.REQUIRED},
    {"type": StageType.PRE_RUNTIME_VERIFICATION, "seq": 6, "name": "Pre-Runtime Verification", "criticality": StageCriticality.REQUIRED, "applicability": StageApplicability.REQUIRED},
    {"type": StageType.BUILD, "seq": 7, "name": "Build", "criticality": StageCriticality.REQUIRED, "applicability": StageApplicability.REQUIRED},
    {"type": StageType.INFRASTRUCTURE_STARTUP, "seq": 8, "name": "Infrastructure Startup", "criticality": StageCriticality.REQUIRED, "applicability": StageApplicability.CONDITIONAL},
    {"type": StageType.APPLICATION_STARTUP, "seq": 9, "name": "Application Startup", "criticality": StageCriticality.REQUIRED, "applicability": StageApplicability.CONDITIONAL},
    {"type": StageType.LIVE_WORKFLOW_TESTING, "seq": 10, "name": "Live Workflow Testing", "criticality": StageCriticality.REQUIRED, "applicability": StageApplicability.REQUIRED},
    {"type": StageType.ARCHITECTURE_PORTABILITY, "seq": 11, "name": "Architecture Portability", "criticality": StageCriticality.RECOMMENDED, "applicability": StageApplicability.OPTIONAL},
    {"type": StageType.PRODUCTION_READINESS, "seq": 12, "name": "Production Readiness", "criticality": StageCriticality.RECOMMENDED, "applicability": StageApplicability.OPTIONAL},
    {"type": StageType.OUTPUT_CORRECTNESS, "seq": 13, "name": "Output Correctness", "criticality": StageCriticality.RECOMMENDED, "applicability": StageApplicability.REQUIRED},
    {"type": StageType.COMPLIANCE, "seq": 14, "name": "Compliance", "criticality": StageCriticality.OPTIONAL, "applicability": StageApplicability.OPTIONAL},
    {"type": StageType.FINAL_ADVISORY_REPORT, "seq": 15, "name": "Final Advisory Report", "criticality": StageCriticality.REQUIRED, "applicability": StageApplicability.REQUIRED},
]

STAGE_PREREQUISITES: dict[StageType, list[StageType]] = {
    StageType.INTAKE: [],
    StageType.PASSIVE_DISCOVERY: [StageType.INTAKE],
    StageType.PLAN_GENERATION: [StageType.PASSIVE_DISCOVERY],
    StageType.POLICY_VALIDATION: [StageType.PLAN_GENERATION],
    StageType.ENVIRONMENT_PROVISIONING: [StageType.POLICY_VALIDATION],
    StageType.DEPENDENCY_INSTALLATION: [StageType.ENVIRONMENT_PROVISIONING],
    StageType.PRE_RUNTIME_VERIFICATION: [StageType.DEPENDENCY_INSTALLATION],
    StageType.BUILD: [StageType.PRE_RUNTIME_VERIFICATION],
    StageType.INFRASTRUCTURE_STARTUP: [StageType.BUILD],
    StageType.APPLICATION_STARTUP: [StageType.INFRASTRUCTURE_STARTUP],
    StageType.LIVE_WORKFLOW_TESTING: [StageType.APPLICATION_STARTUP],
    StageType.ARCHITECTURE_PORTABILITY: [StageType.LIVE_WORKFLOW_TESTING],
    StageType.PRODUCTION_READINESS: [StageType.LIVE_WORKFLOW_TESTING],
    StageType.OUTPUT_CORRECTNESS: [StageType.LIVE_WORKFLOW_TESTING],
    StageType.COMPLIANCE: [StageType.LIVE_WORKFLOW_TESTING],
    StageType.FINAL_ADVISORY_REPORT: [StageType.LIVE_WORKFLOW_TESTING],
}


class FindingSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorClassification(str, Enum):
    NONE = "none"
    URL_VALIDATION = "url_validation"
    ACQUISITION = "acquisition"
    DISCOVERY = "discovery"
    PLAN_GENERATION = "plan_generation"
    POLICY_VALIDATION = "policy_validation"
    PROVISIONING = "provisioning"
    DEPENDENCY = "dependency"
    BUILD = "build"
    RUNTIME = "runtime"
    UNKNOWN = "unknown"

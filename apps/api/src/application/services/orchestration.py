"""Stage orchestration — definitions, progress, status derivation."""

from src.domain.enums import (
    STAGE_DEFINITIONS,
    STAGE_PREREQUISITES,
    MasterJobStatus,
    StageStatus,
    StageType,
)


def get_stage_definitions() -> list[dict]:
    return STAGE_DEFINITIONS


def get_stage_definition(stage_type: StageType) -> dict | None:
    for d in STAGE_DEFINITIONS:
        if d["type"] == stage_type:
            return d
    return None


def get_prerequisites(stage_type: StageType) -> list[StageType]:
    return STAGE_PREREQUISITES.get(stage_type, [])


def compute_progress(stages: list[dict]) -> float:
    """Compute overall progress as a fraction 0.0–1.0 from stage statuses."""
    if not stages:
        return 0.0
    total = len(stages)
    weights = {
        "completed": 1.0,
        "completed_with_findings": 0.9,
        "running": 0.5,
        "paused": 0.25,
        "pending": 0.0,
        "ready": 0.0,
        "failed": 0.0,
        "blocked": 0.0,
        "cancelled": 0.0,
        "skipped_not_applicable": 1.0,
    }
    score = sum(weights.get(s.get("status", "pending"), 0.0) for s in stages)
    return score / total


def derive_job_status(stages: list[dict]) -> MasterJobStatus:
    """Derive the overall master job status from its stages."""
    if not stages:
        return MasterJobStatus.CREATED
    statuses = [s.get("status", "pending") for s in stages]
    if all(s in ("completed", "completed_with_findings", "skipped_not_applicable") for s in statuses):
        if any(s == "completed_with_findings" for s in statuses):
            return MasterJobStatus.COMPLETED_WITH_FINDINGS
        return MasterJobStatus.COMPLETED
    if any(s == "failed" for s in statuses):
        return MasterJobStatus.FAILED
    if any(s == "blocked" for s in statuses):
        return MasterJobStatus.BLOCKED
    if any(s == "paused" for s in statuses):
        return MasterJobStatus.PAUSED
    if any(s == "running" for s in statuses):
        return MasterJobStatus.RUNNING
    if any(s == "cancelled" for s in statuses):
        return MasterJobStatus.CANCELLED
    return MasterJobStatus.CREATED


def get_ready_stages(stages: list[dict]) -> list[dict]:
    """Find stages where all prerequisites are completed."""
    completed_types = {
        StageType(s["stage_type"])
        for s in stages
        if s.get("status") in ("completed", "completed_with_findings", "skipped_not_applicable")
    }
    ready = []
    for s in stages:
        if s.get("status") == "ready":
            ready.append(s)
        elif s.get("status") == "pending":
            stage_type = StageType(s["stage_type"])
            prereqs = get_prerequisites(stage_type)
            if all(p in completed_types for p in prereqs):
                ready.append(s)
    return ready

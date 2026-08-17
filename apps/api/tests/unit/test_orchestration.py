"""Unit tests — stage orchestration: definitions, prerequisites, progress, status."""

from src.domain.enums import (
    MasterJobStatus,
    StageType,
)
from src.application.services.orchestration import (
    get_stage_definitions,
    get_stage_definition,
    get_prerequisites,
    compute_progress,
    derive_job_status,
    get_ready_stages,
)


# ═══════════════════════════════════════════════════════════
# Stage Definitions
# ═══════════════════════════════════════════════════════════

class TestStageDefinitions:
    def test_sixteen_stages_defined(self):
        assert len(get_stage_definitions()) == 16

    def test_first_stage_is_intake(self):
        assert get_stage_definitions()[0]["type"] == StageType.INTAKE

    def test_last_stage_is_final_advisory(self):
        assert get_stage_definitions()[-1]["type"] == StageType.FINAL_ADVISORY_REPORT

    def test_get_stage_definition_by_type(self):
        d = get_stage_definition(StageType.BUILD)
        assert d is not None
        assert d["name"] == "Build"
        assert d["seq"] == 7

    def test_every_definition_has_required_fields(self):
        for d in get_stage_definitions():
            assert "type" in d and "seq" in d and "name" in d


# ═══════════════════════════════════════════════════════════
# Prerequisites
# ═══════════════════════════════════════════════════════════

class TestPrerequisites:
    def test_intake_has_no_prerequisites(self):
        assert get_prerequisites(StageType.INTAKE) == []

    def test_discovery_depends_on_intake(self):
        assert get_prerequisites(StageType.PASSIVE_DISCOVERY) == [StageType.INTAKE]

    def test_build_depends_on_pre_runtime(self):
        assert get_prerequisites(StageType.BUILD) == [StageType.PRE_RUNTIME_VERIFICATION]

    def test_final_report_depends_on_live_testing(self):
        assert get_prerequisites(StageType.FINAL_ADVISORY_REPORT) == [StageType.LIVE_WORKFLOW_TESTING]


# ═══════════════════════════════════════════════════════════
# Progress
# ═══════════════════════════════════════════════════════════

class TestProgress:
    def test_empty_returns_zero(self):
        assert compute_progress([]) == 0.0

    def test_all_completed_returns_one(self):
        stages = [{"status": "completed"} for _ in range(4)]
        assert compute_progress(stages) == 1.0

    def test_half_completed(self):
        stages = [
            {"status": "completed"}, {"status": "completed"},
            {"status": "pending"}, {"status": "pending"},
        ]
        assert compute_progress(stages) == 0.5

    def test_completed_with_findings_partial_weight(self):
        assert compute_progress([{"status": "completed_with_findings"}]) == 0.9

    def test_skipped_counts_as_complete(self):
        assert compute_progress([{"status": "skipped_not_applicable"}]) == 1.0


# ═══════════════════════════════════════════════════════════
# Job Status Derivation
# ═══════════════════════════════════════════════════════════

class TestJobStatus:
    def test_empty_returns_created(self):
        assert derive_job_status([]) == MasterJobStatus.CREATED

    def test_all_completed(self):
        stages = [{"status": "completed"} for _ in range(16)]
        assert derive_job_status(stages) == MasterJobStatus.COMPLETED

    def test_completed_with_findings(self):
        stages = [{"status": "completed"}, {"status": "completed_with_findings"}]
        assert derive_job_status(stages) == MasterJobStatus.COMPLETED_WITH_FINDINGS

    def test_failed(self):
        stages = [{"status": "completed"}, {"status": "failed"}]
        assert derive_job_status(stages) == MasterJobStatus.FAILED

    def test_running(self):
        stages = [{"status": "pending"}, {"status": "running"}]
        assert derive_job_status(stages) == MasterJobStatus.RUNNING

    def test_blocked(self):
        stages = [{"status": "blocked"}]
        assert derive_job_status(stages) == MasterJobStatus.BLOCKED


# ═══════════════════════════════════════════════════════════
# Ready Stage Selection
# ═══════════════════════════════════════════════════════════

class TestReadyStages:
    def test_intake_ready_with_no_prereqs(self):
        stages = [{"stage_type": "00_intake", "status": "pending"}]
        ready = get_ready_stages(stages)
        assert len(ready) == 1

    def test_discovery_not_ready_without_intake(self):
        stages = [
            {"stage_type": "00_intake", "status": "pending"},
            {"stage_type": "01_passive_discovery", "status": "pending"},
        ]
        ready_types = {s["stage_type"] for s in get_ready_stages(stages)}
        assert "01_passive_discovery" not in ready_types

    def test_discovery_ready_after_intake_completed(self):
        stages = [
            {"stage_type": "00_intake", "status": "completed"},
            {"stage_type": "01_passive_discovery", "status": "pending"},
        ]
        ready_types = {s["stage_type"] for s in get_ready_stages(stages)}
        assert "01_passive_discovery" in ready_types

    def test_explicit_ready_status_returned(self):
        stages = [
            {"stage_type": "00_intake", "status": "ready"},
            {"stage_type": "01_passive_discovery", "status": "pending"},
        ]
        ready_types = {s["stage_type"] for s in get_ready_stages(stages)}
        assert "00_intake" in ready_types

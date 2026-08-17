"""Backend unit tests — configuration, domain lifecycle, LLM contract, enums."""

import pytest

from src.domain.enums import (
    ALLOWED_TRANSITIONS,
    RunLifecycle,
    GateStatus,
    FindingSeverity,
    ErrorClassification,
    MasterJobStatus,
    StageType,
)
from src.application.services.lifecycle import (
    can_transition,
    transition,
    is_terminal,
    InvalidTransitionError,
)
from src.infrastructure.llm.fake_provider import FakeLLMProvider, FAKE_SENTINEL


# ═══════════════════════════════════════════════════════════
# Configuration & Secret Redaction
# ═══════════════════════════════════════════════════════════

class TestConfigurationValidation:
    def test_settings_defaults(self, monkeypatch):
        for var in ("SECRET_KEY", "LLM_PROVIDER", "LLM_MODEL", "LLM_API_KEY",
                    "LLM_BASE_URL", "DATABASE_URL", "RUNNER_PROVIDER", "DEV_AUTH_TOKEN"):
            monkeypatch.delenv(var, raising=False)
        from src.infrastructure.config import Settings
        s = Settings(_env_file=None)
        assert s.llm_provider == "fake"
        assert s.database_url is not None
        assert s.secret_key == "change-me-in-production"

    def test_redacted_dict_hides_llm_api_key(self):
        from src.infrastructure.config import Settings
        s = Settings(_env_file=None, llm_api_key="sk-1234567890abcdef")
        d = s.redacted_dict()
        assert d["llm_api_key"] == "***"

    def test_redacted_dict_keeps_non_secret_values(self):
        from src.infrastructure.config import Settings
        s = Settings(_env_file=None, llm_provider="openrouter", debug=True)
        d = s.redacted_dict()
        assert d["llm_provider"] == "openrouter"
        assert d["debug"] is True

    def test_llm_is_configured_false_for_fake(self):
        from src.infrastructure.config import Settings
        s = Settings(_env_file=None, llm_provider="fake", llm_api_key="")
        assert s.llm_is_configured() is False

    def test_llm_is_configured_true_with_real_provider(self):
        from src.infrastructure.config import Settings
        s = Settings(_env_file=None, llm_provider="openrouter", llm_api_key="sk-12345")
        assert s.llm_is_configured() is True


# ═══════════════════════════════════════════════════════════
# Domain Lifecycle Transitions
# ═══════════════════════════════════════════════════════════

class TestLifecycleTransitions:
    VALID_PAIRS = [
        (RunLifecycle.CREATED, RunLifecycle.DISCOVERING),
        (RunLifecycle.DISCOVERING, RunLifecycle.PLAN_READY),
        (RunLifecycle.PLAN_READY, RunLifecycle.AWAITING_APPROVAL),
        (RunLifecycle.AWAITING_APPROVAL, RunLifecycle.APPROVED),
        (RunLifecycle.APPROVED, RunLifecycle.PROVISIONING),
        (RunLifecycle.PROVISIONING, RunLifecycle.EXECUTING),
        (RunLifecycle.EXECUTING, RunLifecycle.VERIFYING),
        (RunLifecycle.VERIFYING, RunLifecycle.REPORTING),
        (RunLifecycle.REPORTING, RunLifecycle.COMPLETED),
        (RunLifecycle.DISCOVERING, RunLifecycle.FAILED),
        (RunLifecycle.CREATED, RunLifecycle.CANCELLED),
    ]

    INVALID_PAIRS = [
        (RunLifecycle.COMPLETED, RunLifecycle.EXECUTING),
        (RunLifecycle.CANCELLED, RunLifecycle.DISCOVERING),
        (RunLifecycle.CREATED, RunLifecycle.COMPLETED),
        (RunLifecycle.EXECUTING, RunLifecycle.CREATED),
    ]

    @pytest.mark.parametrize("frm,to", VALID_PAIRS)
    def test_valid_transitions_allowed(self, frm, to):
        assert can_transition(frm, to) is True
        assert transition(frm, to) == to

    @pytest.mark.parametrize("frm,to", INVALID_PAIRS)
    def test_invalid_transitions_rejected(self, frm, to):
        assert can_transition(frm, to) is False
        with pytest.raises(InvalidTransitionError):
            transition(frm, to)

    def test_terminal_states(self):
        assert is_terminal(RunLifecycle.COMPLETED) is True
        assert is_terminal(RunLifecycle.CANCELLED) is True
        assert is_terminal(RunLifecycle.CREATED) is False

    def test_transition_error_message_lists_allowed(self):
        with pytest.raises(InvalidTransitionError) as exc:
            transition(RunLifecycle.CREATED, RunLifecycle.COMPLETED)
        assert "Cannot transition" in str(exc.value)


# ═══════════════════════════════════════════════════════════
# Fake LLM Provider Contract
# ═══════════════════════════════════════════════════════════

class TestFakeLLMProvider:
    async def test_health_check_returns_true(self):
        provider = FakeLLMProvider()
        assert await provider.health_check() is True

    async def test_analyze_context_includes_sentinel(self):
        provider = FakeLLMProvider()
        result = await provider.analyze_repository_context({})
        assert FAKE_SENTINEL in result["sources"]
        assert "python" in result["languages"]

    async def test_generate_plan_includes_sentinel(self):
        provider = FakeLLMProvider()
        result = await provider.generate_verification_plan({})
        assert result.ecosystem == "python"
        assert len(result.stages) == 2
        all_commands = [c for s in result.stages for c in s["commands"]]
        assert any(FAKE_SENTINEL in c["source"] for c in all_commands)

    async def test_interpret_evidence_includes_sentinel(self):
        provider = FakeLLMProvider()
        result = await provider.interpret_evidence([{}])
        assert len(result.findings) == 1
        assert FAKE_SENTINEL in result.findings[0]["source"]

    async def test_upgrade_recommendations_includes_sentinel(self):
        provider = FakeLLMProvider()
        result = await provider.generate_upgrade_recommendations([{}])
        assert len(result.recommendations) == 1
        assert FAKE_SENTINEL in result.recommendations[0]["source"]

    async def test_call_tracking_and_reset(self):
        provider = FakeLLMProvider()
        await provider.health_check()
        await provider.health_check()
        assert provider.call_count == 2
        provider.reset()
        assert provider.call_count == 0

    def test_sentinel_is_unambiguous_fake_marker(self):
        assert FAKE_SENTINEL == "FAKE_LLM_OUTPUT"
        assert "HERMES" not in FAKE_SENTINEL


# ═══════════════════════════════════════════════════════════
# Enum Integrity
# ═══════════════════════════════════════════════════════════

class TestEnumIntegrity:
    def test_all_lifecycle_states_have_transition_rules(self):
        for state in RunLifecycle:
            assert state in ALLOWED_TRANSITIONS, f"Missing transitions for {state}"

    def test_gate_status_values(self):
        assert GateStatus.PLANNED.value == "planned"
        assert GateStatus.ACTIVE.value == "active"

    def test_finding_severity_values(self):
        assert FindingSeverity.INFO.value == "info"
        assert FindingSeverity.CRITICAL.value == "critical"

    def test_error_classification_has_unknown(self):
        assert ErrorClassification.UNKNOWN.value == "unknown"

    def test_master_job_status_values(self):
        assert MasterJobStatus.CREATED.value == "created"
        assert MasterJobStatus.COMPLETED_WITH_FINDINGS.value == "completed_with_findings"

    def test_stage_type_has_sixteen(self):
        assert len(StageType) == 16

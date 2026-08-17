"""Unit tests — policy engine: rules, evaluation, summary."""

from src.domain.policy_enums import (
    PolicyDecision,
    PolicyOutcome,
    PolicyArea,
    RiskLevel,
    RestrictionType,
    ApprovalScope,
)
from src.application.services.policy_engine import (
    PolicyEngine,
    PolicyRuleDef,
    PolicyRuleEvaluation,
)


# ═══════════════════════════════════════════════════════════
# Policy Rule Definitions
# ═══════════════════════════════════════════════════════════

class TestPolicyRules:
    def test_rule_count(self):
        assert len(PolicyEngine.RULES) >= 30

    def test_rules_have_required_fields(self):
        for rule in PolicyEngine.RULES:
            assert rule.id
            assert rule.name
            assert rule.area
            assert rule.risk_level

    def test_all_four_areas_present(self):
        ids = {r.id[:3] for r in PolicyEngine.RULES}
        assert "SEC" in ids
        assert "COM" in ids
        assert "OPS" in ids
        assert "QLT" in ids

    def test_rule_ids_unique(self):
        ids = [r.id for r in PolicyEngine.RULES]
        assert len(ids) == len(set(ids))


# ═══════════════════════════════════════════════════════════
# Policy Evaluation
# ═══════════════════════════════════════════════════════════

class TestPolicyEvaluation:
    def _evaluate(self, manifest=None, warnings=None):
        engine = PolicyEngine()
        m = manifest if manifest is not None else {"dependency_files": [], "detected_frameworks": []}
        return engine, engine.evaluate(m, discovery_warnings=warnings)

    def test_evaluate_returns_result_per_enabled_rule(self):
        _, results = self._evaluate()
        assert len(results) == len(PolicyEngine.RULES)

    def test_missing_dockerfile_warns(self):
        _, results = self._evaluate()
        ops1 = [r for r in results if r.rule_id == "OPS-001"]
        assert ops1[0].outcome == PolicyOutcome.WARN
        assert ops1[0].decision == PolicyDecision.WARN

    def test_secrets_warning_triggers_sec001(self):
        warnings = [{"warning_type": "sensitive_file"}]
        _, results = self._evaluate(warnings=warnings)
        sec1 = [r for r in results if r.rule_id == "SEC-001"]
        assert sec1[0].outcome == PolicyOutcome.WARN

    def test_clean_manifest_sec001_passes(self):
        _, results = self._evaluate(warnings=[])
        sec1 = [r for r in results if r.rule_id == "SEC-001"]
        assert sec1[0].outcome == PolicyOutcome.PASS

    def test_evaluation_records_rule_metadata(self):
        _, results = self._evaluate()
        for r in results:
            assert r.rule_id
            assert r.rule_name
            assert r.area

    def test_evaluation_is_deterministic(self):
        e1, r1 = self._evaluate()
        e2, r2 = self._evaluate()
        assert [x.outcome for x in r1] == [x.outcome for x in r2]


# ═══════════════════════════════════════════════════════════
# Policy Summary
# ═══════════════════════════════════════════════════════════

class TestPolicySummary:
    def test_summary_totals_match_results(self):
        engine = PolicyEngine()
        results = engine.evaluate({"dependency_files": [], "detected_frameworks": []})
        summary = engine.get_summary(results)
        assert summary["total"] == len(results)
        assert summary["passed"] + summary["warned"] + summary["failed"] == len(results)

    def test_summary_decision_allow_when_no_failures(self):
        engine = PolicyEngine()
        results = engine.evaluate({"dependency_files": ["Dockerfile"], "detected_frameworks": []})
        summary = engine.get_summary(results)
        assert summary["overall_decision"] in ("allow", "warn")

    def test_summary_has_risk_and_approval_fields(self):
        engine = PolicyEngine()
        results = engine.evaluate({"dependency_files": [], "detected_frameworks": []})
        summary = engine.get_summary(results)
        assert "risk_level" in summary
        assert "requires_approval" in summary


# ═══════════════════════════════════════════════════════════
# Policy Domain Enums & Models
# ═══════════════════════════════════════════════════════════

class TestPolicyEnums:
    def test_decision_values(self):
        assert PolicyDecision.ALLOW.value == "allow"
        assert PolicyDecision.DENY.value == "deny"
        assert PolicyDecision.WARN.value == "warn"

    def test_outcome_values(self):
        assert PolicyOutcome.PASS.value == "pass"
        assert PolicyOutcome.FAIL.value == "fail"

    def test_risk_levels(self):
        assert RiskLevel.CRITICAL.value == "critical"
        assert RiskLevel.NONE.value == "none"

    def test_restriction_types(self):
        assert RestrictionType.NETWORK.value == "network"
        assert RestrictionType.FILESYSTEM.value == "filesystem"

    def test_approval_scopes(self):
        assert ApprovalScope.SINGLE_RUN.value == "single_run"
        assert ApprovalScope.GLOBAL.value == "global"

    def test_policy_areas(self):
        assert PolicyArea.SECURITY.value == "security"
        assert PolicyArea.QUALITY.value == "quality"

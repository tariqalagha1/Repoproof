"""Fake LLM provider for testing."""

from .interface import (
    EvidenceInterpretation,
    LLMProvider,
    UpgradeRecommendations,
    VerificationPlanOutput,
)

FAKE_SENTINEL = "FAKE_LLM_OUTPUT"


class FakeLLMProvider(LLMProvider):
    def __init__(self):
        self._calls: list[str] = []

    @property
    def call_count(self) -> int:
        return len(self._calls)

    @property
    def calls(self) -> list[str]:
        return list(self._calls)

    async def health_check(self) -> bool:
        self._calls.append("health_check")
        return True

    async def analyze_repository_context(self, manifest: dict) -> dict:
        self._calls.append("analyze_repository_context")
        return {"ecosystem": "python", "frameworks": ["fastapi"], "languages": ["python"], "sources": [FAKE_SENTINEL]}

    async def generate_verification_plan(self, context: dict) -> VerificationPlanOutput:
        self._calls.append("generate_verification_plan")
        return VerificationPlanOutput(
            ecosystem="python",
            stages=[
                {"name": "setup", "seq": 0, "commands": [{"command": "pip install -e .", "source": FAKE_SENTINEL}]},
                {"name": "test", "seq": 1, "commands": [{"command": "pytest", "source": FAKE_SENTINEL}]},
            ],
        )

    async def interpret_evidence(self, evidence: list[dict]) -> EvidenceInterpretation:
        self._calls.append("interpret_evidence")
        return EvidenceInterpretation(
            findings=[{"severity": "low", "title": "No issues found", "source": FAKE_SENTINEL}],
            recommendations=[{"title": "Keep up the good work", "source": FAKE_SENTINEL}],
        )

    async def generate_upgrade_recommendations(self, findings: list[dict]) -> UpgradeRecommendations:
        self._calls.append("generate_upgrade_recommendations")
        return UpgradeRecommendations(
            recommendations=[{"title": "Update dependencies", "source": FAKE_SENTINEL}],
        )

    def reset(self):
        self._calls.clear()

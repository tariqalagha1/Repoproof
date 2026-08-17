"""LLM provider abstract interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VerificationPlanOutput:
    stages: list[dict]
    ecosystem: str


@dataclass
class EvidenceInterpretation:
    findings: list[dict]
    recommendations: list[dict]


@dataclass
class UpgradeRecommendations:
    recommendations: list[dict]


class LLMProvider(ABC):
    @abstractmethod
    async def health_check(self) -> bool:
        ...

    @abstractmethod
    async def analyze_repository_context(self, manifest: dict) -> dict:
        ...

    @abstractmethod
    async def generate_verification_plan(self, context: dict) -> VerificationPlanOutput:
        ...

    @abstractmethod
    async def interpret_evidence(self, evidence: list[dict]) -> EvidenceInterpretation:
        ...

    @abstractmethod
    async def generate_upgrade_recommendations(self, findings: list[dict]) -> UpgradeRecommendations:
        ...

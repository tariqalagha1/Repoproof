"""Phase 5 — Compatibility Score Engine.

Produces a green/yellow/red compatibility rating based on:
- Security scan results
- Dependency audit findings
- Version check results
- Build/test success
- Execution exit codes
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Score(Enum):
    GREEN = "green"     # Safe to use — all checks pass
    YELLOW = "yellow"   # Caution — some issues found
    RED = "red"         # Unsafe — critical issues


@dataclass
class CompatibilityReport:
    overall_score: Score = Score.GREEN
    security_score: Score = Score.GREEN
    dependency_score: Score = Score.GREEN
    version_score: Score = Score.GREEN
    build_score: Score = Score.GREEN
    test_score: Score = Score.GREEN

    # Details
    secrets_found: int = 0
    vulnerabilities: int = 0
    critical_vulns: int = 0
    version_mismatches: int = 0
    build_passed: bool = False
    tests_passed: int = 0
    tests_failed: int = 0

    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


def compute_compatibility(
    secrets_count: int = 0,
    vulnerabilities: int = 0,
    critical_vulns: int = 0,
    version_mismatches: int = 0,
    build_passed: bool = False,
    tests_passed: int = 0,
    tests_failed: int = 0,
    syntax_ok: bool = True,
    exit_code: int = 0,
) -> CompatibilityReport:
    report = CompatibilityReport()

    # ── Security Score ──────────────────────────────────
    if secrets_count > 0:
        report.security_score = Score.RED
        report.warnings.append(f"{secrets_count} hardcoded secrets found")
        report.recommendations.append("Remove hardcoded secrets and use environment variables or a secrets manager")
    else:
        report.security_score = Score.GREEN
    report.secrets_found = secrets_count

    # ── Dependency Score ────────────────────────────────
    if critical_vulns > 0:
        report.dependency_score = Score.RED
        report.warnings.append(f"{critical_vulns} critical vulnerabilities in dependencies")
        report.recommendations.append("Update dependencies with critical vulnerabilities immediately")
    elif vulnerabilities > 5:
        report.dependency_score = Score.YELLOW
        report.warnings.append(f"{vulnerabilities} vulnerable dependencies found")
        report.recommendations.append("Review and update vulnerable dependencies")
    elif vulnerabilities > 0:
        report.dependency_score = Score.YELLOW
        report.warnings.append(f"{vulnerabilities} low-severity vulnerabilities found")
    else:
        report.dependency_score = Score.GREEN
    report.vulnerabilities = vulnerabilities
    report.critical_vulns = critical_vulns

    # ── Version Score ───────────────────────────────────
    if version_mismatches > 0:
        report.version_score = Score.YELLOW
        report.warnings.append(f"{version_mismatches} runtime version mismatches")
        report.recommendations.append("Align runtime versions with repository requirements")
    else:
        report.version_score = Score.GREEN
    report.version_mismatches = version_mismatches

    # ── Build Score ─────────────────────────────────────
    if not syntax_ok:
        report.build_score = Score.RED
        report.warnings.append("Syntax errors found in source code")
    elif build_passed:
        report.build_score = Score.GREEN
    else:
        report.build_score = Score.YELLOW
    report.build_passed = build_passed

    # ── Test Score ──────────────────────────────────────
    if tests_failed > 0:
        report.test_score = Score.RED if tests_passed == 0 else Score.YELLOW
        report.warnings.append(f"{tests_failed} tests failed out of {tests_passed + tests_failed}")
    elif tests_passed > 0:
        report.test_score = Score.GREEN
    else:
        report.test_score = Score.YELLOW
    report.tests_passed = tests_passed
    report.tests_failed = tests_failed

    # ── Overall Score (worst of all) ────────────────────
    scores = [
        report.security_score,
        report.dependency_score,
        report.version_score,
        report.build_score,
        report.test_score,
    ]
    if Score.RED in scores:
        report.overall_score = Score.RED
    elif Score.YELLOW in scores:
        report.overall_score = Score.YELLOW
    else:
        report.overall_score = Score.GREEN

    return report


def score_emoji(score: Score) -> str:
    if score == Score.GREEN:
        return "🟢"
    elif score == Score.YELLOW:
        return "🟡"
    return "🔴"


def score_badge(score: Score) -> str:
    return {
        Score.GREEN: "✅ SAFE",
        Score.YELLOW: "⚠️ CAUTION",
        Score.RED: "🚫 UNSAFE",
    }[score]

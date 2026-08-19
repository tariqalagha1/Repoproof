"""Phase 2 — Dependency Auditor.

Audits third-party packages for known vulnerabilities.
Uses pip-audit for Python, npm audit for Node.js.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AuditResult:
    ecosystem: str
    total_packages: int = 0
    vulnerable: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    findings: list[dict] = field(default_factory=list)
    raw_output: str = ""
    success: bool = False


async def audit_dependencies(
    project_root: Path,
    container_id: str | None = None,
    runner=None,
) -> list[AuditResult]:
    """Run dependency audits for all detected ecosystems.

    Args:
        project_root: Path to extracted repository
        container_id: Docker container ID if running in container
        runner: DockerSDKRunner instance

    Returns:
        List of AuditResult per ecosystem found.
    """
    results: list[AuditResult] = []

    # Detect ecosystems
    ecosystems = _detect_ecosystems(project_root)

    for eco in ecosystems:
        result = await _audit_ecosystem(eco, project_root, container_id, runner)
        results.append(result)

    return results


def _detect_ecosystems(root: Path) -> list[str]:
    ecosystems = []
    if (root / "requirements.txt").exists() or (root / "pyproject.toml").exists() or (root / "setup.py").exists():
        ecosystems.append("python")
    if (root / "package.json").exists():
        ecosystems.append("node")
    return ecosystems


async def _audit_ecosystem(
    ecosystem: str,
    root: Path,
    container_id: str | None,
    runner,
) -> AuditResult:
    if ecosystem == "python":
        return await _audit_python(root, container_id, runner)
    elif ecosystem == "node":
        return await _audit_node(root, container_id, runner)
    return AuditResult(ecosystem=ecosystem, success=False)


async def _audit_python(
    root: Path, container_id: str | None, runner,
) -> AuditResult:
    result = AuditResult(ecosystem="python")
    # pip-audit exits non-zero (1) when it finds vulnerabilities, so a non-zero
    # exit is NOT "skipped" — the JSON report is still on stdout.
    cmd = "python3 -m pip install pip-audit --break-system-packages >/dev/null 2>&1 && python3 -m pip_audit --path . --format json 2>/dev/null"

    if container_id and runner:
        exit_code, stdout, stderr = runner.exec_run(container_id, f"cd /workspace/source && {cmd}", timeout=240)
    else:
        # Local fallback
        import subprocess
        r = subprocess.run(["sh", "-c", f"cd {root} && {cmd}"], capture_output=True, text=True, timeout=240)
        exit_code = r.returncode
        stdout = r.stdout

    result.raw_output = stdout

    if not stdout.strip():
        result.success = False
        return result

    # Parse pip-audit JSON. Vulnerabilities are nested under each dependency's
    # "vulns" array; pip-audit does not expose a per-vuln severity field.
    try:
        import json
        data = json.loads(stdout)
        deps = data.get("dependencies", [])
        result.total_packages = len(deps)
        for dep in deps:
            for vuln in dep.get("vulns", []):
                result.vulnerable += 1
                result.findings.append({
                    "package": dep.get("name", ""),
                    "version": dep.get("version", ""),
                    "severity": "unknown",
                    "advisory": ", ".join(vuln.get("aliases", []) or [vuln.get("id", "")]),
                })
        result.success = True
    except Exception:
        result.success = False

    return result


async def _audit_node(
    root: Path, container_id: str | None, runner,
) -> AuditResult:
    result = AuditResult(ecosystem="node")
    cmd = "npm audit --json 2>/dev/null || echo 'AUDIT_SKIPPED'"

    if container_id and runner:
        exit_code, stdout, stderr = runner.exec_run(container_id, f"cd /workspace/source && {cmd}", timeout=120)
    else:
        import subprocess
        r = subprocess.run(["sh", "-c", f"cd {root} && {cmd}"], capture_output=True, text=True, timeout=120)
        exit_code = r.returncode
        stdout = r.stdout

    result.raw_output = stdout

    if "AUDIT_SKIPPED" in stdout or not stdout.strip():
        return result

    try:
        import json
        data = json.loads(stdout)
        vulns = data.get("vulnerabilities", {})
        result.total_packages = len(data.get("dependencies", {}))
        for name, info in vulns.items():
            result.vulnerable += 1
            sev = info.get("severity", "low").lower()
            if sev == "critical": result.critical += 1
            elif sev == "high": result.high += 1
            elif sev == "moderate": result.medium += 1
            else: result.low += 1
            result.findings.append({
                "package": name,
                "version": info.get("version", ""),
                "severity": sev,
                "advisory": info.get("advisory", ""),
            })
        result.success = True
    except Exception:
        result.success = False

    return result

"""Phase 2 — Version Checker.

Compares repository runtime requirements against host/runner versions.
Detects mismatches in Python, Node, and other runtime versions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class VersionCheckResult:
    ecosystem: str
    repo_requires: str = ""
    runner_provides: str = ""
    compatible: bool = False
    severity: str = "ok"  # ok, warning, error
    message: str = ""


async def check_versions(
    project_root: Path,
    container_id: str | None = None,
    runner=None,
) -> list[VersionCheckResult]:
    results = []

    # Check Python version
    py_result = await _check_python_version(project_root, container_id, runner)
    if py_result:
        results.append(py_result)

    # Check Node version
    node_result = await _check_node_version(project_root, container_id, runner)
    if node_result:
        results.append(node_result)

    return results


async def _check_python_version(
    root: Path, container_id: str | None, runner,
) -> VersionCheckResult | None:
    # Look for python version requirement
    requires = ""
    for fname in ["pyproject.toml", "setup.py", "setup.cfg", ".python-version"]:
        path = root / fname
        if path.exists():
            content = path.read_text(errors="replace")[:2000]
            if "requires-python" in content.lower():
                for line in content.split("\n"):
                    if "python" in line.lower() and ("=" in line or ">" in line or "<" in line):
                        requires = line.strip()[:100]
                        break
            break

    if not requires:
        return None

    # Get runner Python version
    provides = ""
    if container_id and runner:
        _, stdout, _ = runner.exec_run(container_id, "python3 --version")
        provides = stdout.strip()
    else:
        import sys
        provides = f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    compatible = _version_loosely_matches(requires, provides)

    return VersionCheckResult(
        ecosystem="python",
        repo_requires=requires,
        runner_provides=provides,
        compatible=compatible,
        severity="ok" if compatible else "warning",
        message="Python version matches" if compatible else f"Version mismatch: repo needs {requires}, runner has {provides}",
    )


async def _check_node_version(
    root: Path, container_id: str | None, runner,
) -> VersionCheckResult | None:
    pkg = root / "package.json"
    if not pkg.exists():
        return None

    try:
        import json
        data = json.loads(pkg.read_text()[:10000])
        engines = data.get("engines", {})
        requires = engines.get("node", "")
        if not requires:
            return None
    except Exception:
        return None

    provides = ""
    if container_id and runner:
        _, stdout, _ = runner.exec_run(container_id, "node --version")
        provides = stdout.strip()
    else:
        import subprocess
        r = subprocess.run(["node", "--version"], capture_output=True, text=True)
        provides = r.stdout.strip()

    compatible = _version_loosely_matches(requires, provides)

    return VersionCheckResult(
        ecosystem="node",
        repo_requires=requires,
        runner_provides=provides,
        compatible=compatible,
        severity="ok" if compatible else "warning",
        message="Node version matches" if compatible else f"Version mismatch: repo needs {requires}, runner has {provides}",
    )


def _version_loosely_matches(requires: str, provides: str) -> bool:
    """Simple version check — returns True if likely compatible."""
    if not requires or not provides:
        return True
    # Extract major.minor
    import re
    req_nums = re.findall(r'(\d+)\.(\d+)', requires)
    prov_nums = re.findall(r'(\d+)\.(\d+)', provides)
    if req_nums and prov_nums:
        req_major = int(req_nums[0][0])
        req_minor = int(req_nums[0][1])
        prov_major = int(prov_nums[0][0])
        prov_minor = int(prov_nums[0][1])
        # Major must match, minor within 2
        if prov_major != req_major:
            return False
        if abs(prov_minor - req_minor) > 2:
            return False
    return True

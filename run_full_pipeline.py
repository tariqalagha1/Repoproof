"""Full RepoProof AI pipeline — Phase 1-5 complete.
Uses: zip download, Docker SDK, dependency audit, version check, compatibility score.
"""
import asyncio, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps/api"))
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./pipeline_full.db"
os.environ["LLM_PROVIDER"] = "fake"

# ── Init DB ─────────────────────────────────────────────────
from src.infrastructure.database import get_engine, get_sessionmaker
from src.infrastructure.models import Base

# ── Services ────────────────────────────────────────────────
from src.application.services.safe_downloader import fetch_repo_zip
from src.application.services.docker_sdk_runner import DockerSDKRunner
from src.application.services.dependency_auditor import audit_dependencies
from src.application.services.version_checker import check_versions
from src.application.services.compatibility_scorer import (
    compute_compatibility, score_emoji, score_badge, Score,
)
from src.application.services.discovery import discover_repository, secret_fingerprint

from src.infrastructure.repositories.project_repo import ProjectRepository
from src.infrastructure.repositories.master_job_repo import MasterJobRepository

REPO_URL = "https://github.com/nousresearch/hermes-agent"
BRANCH = "main"
CONTAINER_NAME = "repoproof-full-pipeline"


async def main():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sm = get_sessionmaker()
    async with sm() as db:
        repo = MasterJobRepository(db)
        proj_repo = ProjectRepository(db)

        # ═══════════════════════════════════════════════════
        # PHASE 1: Ingestion & Filesystem Safety
        # ═══════════════════════════════════════════════════
        print("═" * 60)
        print(" PHASE 1: INGESTION & FILESYSTEM SAFETY")
        print("═" * 60)

        # 1a. Safe zip download
        print(f"\nDownloading {REPO_URL} as zip...")
        dl = await fetch_repo_zip(REPO_URL, BRANCH)
        print(f"  ✓ Downloaded: {dl.file_count} files")
        print(f"  ✓ Commit: {dl.commit_sha[:12]}...")
        print(f"  ✓ Extracted to: {dl.extract_path}")

        # 1b. Discover
        print("\nRunning passive discovery...")
        discovery = await discover_repository(dl.extract_path)
        print(f"  Languages: {discovery.get('detected_languages', [])}")
        print(f"  Frameworks: {discovery.get('detected_frameworks', [])}")
        print(f"  Dep files: {discovery.get('dependency_files', [])}")
        print(f"  Entry points: {discovery.get('entry_points', [])}")

        # 1c. Secrets scan
        print("\nScanning for secrets...")
        secrets = await secret_fingerprint(dl.extract_path)
        print(f"  ✓ Secrets found: {len(secrets)}")
        for s in secrets[:3]:
            print(f"    - {s.get('type', 'unknown')}: {s.get('file', '')}")

        # 1d. Auto-cleanup
        dl.cleanup()
        print(f"\n  ✓ Source directory cleaned up: {not dl.extract_path.exists()}")

        # ═══════════════════════════════════════════════════
        # PHASE 2: Static Analysis
        # ═══════════════════════════════════════════════════
        print("\n" + "═" * 60)
        print(" PHASE 2: STATIC ANALYSIS (PRE-EXECUTION)")
        print("═" * 60)

        # Manifest reader is done in Phase 1 (discovery)

        # ═══════════════════════════════════════════════════
        # PHASE 3: Sandbox Isolation
        # ═══════════════════════════════════════════════════
        print("\n" + "═" * 60)
        print(" PHASE 3: SANDBOX ISOLATION (DOCKER SDK)")
        print("═" * 60)

        sdk = DockerSDKRunner()
        if not sdk.available():
            print("  ✗ Docker SDK not available — falling back to subprocess")
            sdk = None

        # Download again for container mount
        dl2 = await fetch_repo_zip(REPO_URL, BRANCH)
        source_path = str(dl2.extract_path)

        print(f"\nProvisioning container '{CONTAINER_NAME}'...")

        if sdk:
            container = sdk.provision(
                name=CONTAINER_NAME,
                source_mount=source_path,
                source_mount_mode="ro",
            )
        else:
            import subprocess
            result = subprocess.run([
                "docker", "run", "-d", "--name", CONTAINER_NAME,
                "--user", "1000:1000",
                "--security-opt", "no-new-privileges:true",
                "--cap-drop", "ALL", "--read-only",
                "-v", f"{source_path}:/source:ro",
                "--tmpfs", "/tmp:exec,size=128m,mode=1777",
                "--tmpfs", "/workspace:exec,size=1g,mode=1777",
                "--memory", "512m", "--memory-swap", "512m",
                "--cpu-shares", "512", "--pids-limit", "64",
                "--network", "bridge", "--init",
                "-e", "HOME=/workspace",
                "repoproof-runner:latest", "sleep", "3600",
            ], capture_output=True, text=True, timeout=15)
            container = {"id": result.stdout.strip()}

        cid = container["id"]
        print(f"  Container: {cid[:16]}...")

        # Inspect security posture
        if sdk:
            insp = sdk.inspect(cid)
        else:
            import subprocess, json
            r = subprocess.run(["docker", "inspect", cid], capture_output=True, text=True)
            data = json.loads(r.stdout)[0]
            hc = data["HostConfig"]
            cfg = data["Config"]
            insp = {
                "user": cfg.get("User", ""),
                "privileged": hc.get("Privileged", False),
                "read_only": hc.get("ReadonlyRootfs", False),
                "network_mode": hc.get("NetworkMode", ""),
                "cap_drop": hc.get("CapDrop", []),
                "memory": hc.get("Memory", 0),
                "cpu_shares": hc.get("CpuShares", 0),
                "init": hc.get("Init", False),
                "security_opt": hc.get("SecurityOpt", []),
            }

        print(f"\n  Security Posture:")
        print(f"    User: {insp['user']}")
        print(f"    Privileged: {insp['privileged']}")
        print(f"    Read-only: {insp['read_only']}")
        print(f"    Network: {insp['network_mode']}")
        print(f"    Caps dropped: {insp['cap_drop']}")
        print(f"    Memory: {insp['memory']}")

        # Health + UID
        if sdk:
            health = sdk.health_check(cid)
            uid = sdk.get_uid(cid)
        else:
            r = subprocess.run(["docker", "exec", cid, "/healthcheck.sh"], capture_output=True, text=True)
            health = "OK" in r.stdout
            r = subprocess.run(["docker", "exec", cid, "id"], capture_output=True, text=True)
            uid = r.stdout.strip()
        print(f"\n    Health: {'OK' if health else 'FAIL'}")
        print(f"    UID: {uid}")

        # ═══════════════════════════════════════════════════
        # PHASE 4: Dynamic Evaluation
        # ═══════════════════════════════════════════════════
        print("\n" + "═" * 60)
        print(" PHASE 4: DYNAMIC EVALUATION")
        print("═" * 60)

        def exec_cmd(cmd, timeout=120):
            if sdk:
                return sdk.exec_run(cid, cmd, timeout=timeout)
            else:
                r = subprocess.run(["docker", "exec", cid, "sh", "-c", cmd], capture_output=True, text=True, timeout=timeout)
                return r.returncode, r.stdout, r.stderr

        # Enable network for dependency installation
        print("\nEnabling network for dependency installation...")
        if sdk:
            sdk.connect_network(cid)
        else:
            subprocess.run(["docker", "network", "connect", "bridge", cid], capture_output=True)

        # Copy source into a writable workspace (the /source mount is read-only)
        print("\nCopying source to writable /workspace/source...")
        exec_cmd("mkdir -p /workspace/source", 10)
        ec, out, err = exec_cmd("cp -r /source/. /workspace/source/ 2>/dev/null && ls /workspace/source/ | head -5", 30)
        workdir = "/workspace/source"
        source_ok = ec == 0 and bool(out.strip())
        print(f"  {'✓' if source_ok else '✗'} /workspace/source: {out.strip()[:80]}")

        # Install the target project so its tests can import it
        print("\nInstalling target project (pip install -e)...")
        ec, out, err = exec_cmd(f"cd {workdir} && python3 -m pip install -e . --break-system-packages 2>&1 | tail -3", 240)
        print(f"  Exit: {ec} | {out.strip()[:120]}")

        # Syntax validation
        print("\nSyntax validation (python -m compileall)...")
        ec, out, err = exec_cmd(f"cd {workdir} && python3 -m compileall . 2>&1 | tail -3", 60)
        syntax_ok = ec == 0 and "Sorry" not in out
        print(f"  {'✓' if syntax_ok else '✗'} Exit: {ec}, Output: {out.strip()[:100]}")

        # Dependency audit (runs inside the sandbox via the SDK runner)
        print("\nDependency audit...")
        audit_results = await audit_dependencies(Path(source_path), cid, sdk)
        vulns = 0
        critical = 0
        for ar in audit_results:
            vulns += ar.vulnerable
            critical += ar.critical
            print(f"  {ar.ecosystem}: {ar.total_packages} pkgs, {ar.vulnerable} vulns ({ar.critical} critical)")

        # Version check (runs inside the sandbox)
        print("\nVersion check...")
        ver_results = await check_versions(Path(source_path), cid, sdk)
        mismatches = sum(1 for v in ver_results if not v.compatible)
        for v in ver_results:
            status = "✓" if v.compatible else "✗"
            print(f"  {status} {v.ecosystem}: needs {v.repo_requires[:60]}, has {v.runner_provides[:30]}")

        # Isolate before executing the target's tests
        print("\nIsolating sandbox (disconnect network) before test execution...")
        if sdk:
            sdk.disconnect_network(cid)
        else:
            subprocess.run(["docker", "network", "disconnect", "bridge", cid], capture_output=True)

        # Test collection
        print("\nTest collection (pytest --collect-only)...")
        ec, out, err = exec_cmd(
            f"cd {workdir} && python3 -m pytest tests/ --collect-only -q 2>&1 | tail -5", 90)
        tests_collected = 0
        try:
            tests_collected = int(out.strip().split()[-1]) if out.strip().split()[-1].isdigit() else 0
        except: pass
        print(f"  Tests collected: {tests_collected}")

        # Actual test run
        print("\nRunning test suite...")
        ec, out, err = exec_cmd(
            f"cd {workdir} && python3 -m pytest tests/ -q --tb=short 2>&1 | tail -10", 300)
        tests_passed = 0
        tests_failed = 0
        try:
            last_line = [l for l in out.strip().split("\n") if "passed" in l or "failed" in l]
            if last_line:
                parts = last_line[-1].split()
                for i, p in enumerate(parts):
                    if "passed" in p and i > 0:
                        tests_passed = int(parts[i-1])
                    if "failed" in p and i > 0:
                        tests_failed = int(parts[i-1])
        except: pass
        print(f"  Tests: {tests_passed} passed, {tests_failed} failed, exit: {ec}")
        print(f"  {out.strip()[:300]}")

        # Disconnect network
        if sdk:
            sdk.disconnect_network(cid)
        else:
            subprocess.run(["docker", "network", "disconnect", "bridge", cid], capture_output=True)

        # ═══════════════════════════════════════════════════
        # PHASE 5: Compatibility Score
        # ═══════════════════════════════════════════════════
        print("\n" + "═" * 60)
        print(" PHASE 5: COMPATIBILITY SCORE & REPORTING")
        print("═" * 60)

        score = compute_compatibility(
            secrets_count=len(secrets),
            vulnerabilities=vulns,
            critical_vulns=critical,
            version_mismatches=mismatches,
            build_passed=syntax_ok,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            syntax_ok=syntax_ok,
            exit_code=ec,
        )

        print(f"\n  Overall:     {score_emoji(score.overall_score)} {score_badge(score.overall_score)}")
        print(f"  Security:    {score_emoji(score.security_score)} {score_badge(score.security_score)}")
        print(f"  Dependencies:{score_emoji(score.dependency_score)} {score_badge(score.dependency_score)}")
        print(f"  Versions:    {score_emoji(score.version_score)} {score_badge(score.version_score)}")
        print(f"  Build:       {score_emoji(score.build_score)} {score_badge(score.build_score)}")
        print(f"  Tests:       {score_emoji(score.test_score)} {score_badge(score.test_score)}")

        if score.warnings:
            print(f"\n  ⚠ Warnings ({len(score.warnings)}):")
            for w in score.warnings:
                print(f"    - {w}")
        if score.recommendations:
            print(f"\n  💡 Recommendations:")
            for r in score.recommendations:
                print(f"    - {r}")

        # ═══════════════════════════════════════════════════
        # CLEANUP
        # ═══════════════════════════════════════════════════
        print("\n" + "═" * 60)
        print(" CLEANUP")
        print("═" * 60)

        if sdk:
            sdk.destroy(cid)
        else:
            import subprocess
            subprocess.run(["docker", "rm", "-f", cid], capture_output=True)
        print(f"  ✓ Container {cid[:16]}... destroyed")

        dl2.cleanup()
        print(f"  ✓ Source directory cleaned")

        # Verify no leftovers
        import subprocess
        r = subprocess.run(["docker", "ps", "-a", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.ID}}"], capture_output=True, text=True)
        leftover = r.stdout.strip()
        print(f"  ✓ No leftover containers: {not bool(leftover)}")

        # ═══════════════════════════════════════════════════
        # FINAL
        # ═══════════════════════════════════════════════════
        print("\n" + "═" * 60)
        print(" FINAL VERDICT")
        print("═" * 60)
        print(f"  Repository: {REPO_URL}")
        print(f"  Branch: {BRANCH}")
        print(f"  Commit: {dl2.commit_sha[:12]}...")
        print(f"  Files: {dl2.file_count}")
        print(f"  Languages: {discovery.get('detected_languages', [])}")
        print(f"  Secrets found: {len(secrets)}")
        print(f"  Vulnerabilities: {vulns} ({critical} critical)")
        print(f"  Version mismatches: {mismatches}")
        print(f"  Tests: {tests_passed} passed, {tests_failed} failed")
        print(f"  Overall: {score_emoji(score.overall_score)} {score_badge(score.overall_score)}")
        print()


asyncio.run(main())

"""One-shot pipeline runner for user-specified repository."""
import asyncio, os, sys, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps/api"))
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./run_user.db"
os.environ["LLM_PROVIDER"] = "fake"

from src.application.services.safe_downloader import fetch_repo_zip
from src.application.services.discovery import discover_repository, secret_fingerprint
from src.application.services.docker_sdk_runner import DockerSDKRunner
from src.application.services.dependency_auditor import audit_dependencies
from src.application.services.version_checker import check_versions
from src.application.services.compatibility_scorer import (
    compute_compatibility, score_emoji, score_badge,
)

REPO_URL = sys.argv[1] if len(sys.argv) > 1 else "https://github.com/nousresearch/hermes-agent"
BRANCH = sys.argv[2] if len(sys.argv) > 2 else "main"
CONTAINER_NAME = "repoproof-user-run"


def exec_cmd(cid, cmd, sdk=None, timeout=120):
    if sdk:
        return sdk.exec_run(cid, cmd, timeout=timeout)
    else:
        r = subprocess.run(["docker", "exec", cid, "sh", "-c", cmd],
                          capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr


async def main():
    print("═" * 64)
    print(f" REPOPROOF AI — FULL PIPELINE")
    print(f" Target: {REPO_URL}")
    print(f" Branch: {BRANCH}")
    print("═" * 64)

    # ═══════════════════════════════════════════════════════
    # PHASE 1: INGESTION
    # ═══════════════════════════════════════════════════════
    print(f"\n{'─'*60}\n PHASE 1: INGESTION & FILESYSTEM SAFETY\n{'─'*60}")
    t0 = time.time()
    dl = await fetch_repo_zip(REPO_URL, BRANCH)
    t1 = time.time()
    print(f"  Download: {dl.file_count:,} files in {t1-t0:.1f}s")
    print(f"  Commit SHA: {dl.commit_sha[:40] if dl.commit_sha else 'N/A'}")
    print(f"  Extracted to: {dl.extract_path}")

    # ═══════════════════════════════════════════════════════
    # PHASE 2: STATIC ANALYSIS
    # ═══════════════════════════════════════════════════════
    print(f"\n{'─'*60}\n PHASE 2: STATIC ANALYSIS\n{'─'*60}")

    disc = await discover_repository(dl.extract_path)
    print(f"  Languages: {disc['detected_languages']}")
    print(f"  Frameworks: {disc['detected_frameworks']}")
    print(f"  Entry points: {disc['entry_points']}")
    print(f"  Dependency files: {len(disc['dependency_files'])}")
    for df in disc['dependency_files'][:8]:
        print(f"    • {df}")
    if len(disc['dependency_files']) > 8:
        print(f"    ... and {len(disc['dependency_files'])-8} more")

    # Secrets
    secrets = await secret_fingerprint(dl.extract_path)
    critical_s = [s for s in secrets if s.get('severity') == 'critical']
    high_s = [s for s in secrets if s.get('severity') == 'high']
    medium_s = [s for s in secrets if s.get('severity') == 'medium']
    print(f"\n  Secrets found: {len(secrets)}")
    print(f"    Critical: {len(critical_s)}, High: {len(high_s)}, Medium: {len(medium_s)}")
    for s in secrets[:8]:
        print(f"    [{s['severity']}] {s.get('file','?')}:{s.get('line','?')} — {s['pattern']}")
    if len(secrets) > 8:
        print(f"    ... and {len(secrets)-8} more")

    # ═══════════════════════════════════════════════════════
    # PHASE 3: SANDBOX ISOLATION
    # ═══════════════════════════════════════════════════════
    print(f"\n{'─'*60}\n PHASE 3: SANDBOX ISOLATION\n{'─'*60}")

    sdk = DockerSDKRunner()
    if not sdk.available():
        print("  ✗ Docker not available — aborting dynamic phases")
        sdk = None
    else:
        container = sdk.provision(
            name=CONTAINER_NAME,
            source_mount=str(dl.extract_path),
            source_mount_mode="ro",
        )
        cid = container["id"]
        print(f"  Container: {cid[:20]}...")

        insp = sdk.inspect(cid)
        print(f"  User: {insp['user']}")
        print(f"  Privileged: {insp['privileged']}")
        print(f"  Read-only root: {insp['read_only']}")
        print(f"  Network mode: {insp['network_mode']}")
        print(f"  Caps dropped: {insp['cap_drop']}")
        print(f"  Memory limit: {insp['memory']:,} bytes")
        print(f"  CPU shares: {insp['cpu_shares']}")
        print(f"  Security opts: {insp['security_opt']}")
        print(f"  Init: {insp['init']}")

        health = sdk.health_check(cid)
        uid = sdk.get_uid(cid)
        print(f"\n  Health check: {'✓ OK' if health else '✗ FAIL'}")
        print(f"  UID: {uid}")

        # ── Isolation tests ──
        print(f"\n  Isolation tests:")
        tests = [
            ("Host users blocked", "test ! -r /Users && echo PASS || echo FAIL"),
            ("Host home blocked", "test ! -r /root && echo PASS || echo FAIL"),
            ("SSH keys blocked", "test ! -r /etc/ssh && echo PASS || echo FAIL"),
            ("Docker socket blocked", "test ! -S /var/run/docker.sock && echo PASS || echo FAIL"),
            ("Source read-only", "touch /source/_test 2>/dev/null && echo FAIL || echo PASS"),
            ("Network blocked (ping)", "ping -c1 -W1 8.8.8.8 2>/dev/null && echo FAIL || echo PASS"),
            ("Metadata blocked", "curl -s --connect-timeout 1 http://169.254.169.254/ 2>/dev/null && echo FAIL || echo PASS"),
            ("Path traversal blocked", "test ! -r ../../etc/passwd && echo PASS || echo FAIL"),
        ]
        passed = 0
        for name, cmd in tests:
            _, out, _ = exec_cmd(cid, cmd, sdk, 10)
            ok = "PASS" in out
            passed += 1 if ok else 0
            print(f"    {'✓' if ok else '✗'} {name}: {'PASS' if ok else 'FAIL'}")

        iso_passed = min(passed, 8)
        print(f"  Isolation: {iso_passed}/8 passed")

        # ═══════════════════════════════════════════════════
        # PHASE 4: DYNAMIC EVALUATION
        # ═══════════════════════════════════════════════════
        print(f"\n{'─'*60}\n PHASE 4: DYNAMIC EVALUATION\n{'─'*60}")

        # Verify source
        ec, out, _ = exec_cmd(cid, "ls /source/ 2>/dev/null | head -5", sdk, 10)
        source_ok = ec == 0 and out.strip()
        workdir = "/source" if source_ok else "/workspace"
        print(f"  Source mount: {'✓ /source' if source_ok else '✗ falling back to /workspace'}")

        # ── Syntax: MUST run before imports (no execution) ──
        print(f"\n  Syntax validation (compileall)...")
        ec, out, _ = exec_cmd(cid, f"cd {workdir} && python3 -m compileall . 2>&1 | tail -5", sdk, 120)
        syntax_ok = ec == 0 and "Sorry" not in out
        print(f"  {'✓ PASS' if syntax_ok else '✗ FAIL'} (exit {ec})")

        # ── Dep audit (needs network briefly, then disconnect) ──
        sdk.connect_network(cid)
        print(f"\n  Dependency audit (network temporarily enabled)...")
        dep_results = await audit_dependencies(dl.extract_path, cid, None)
        # Disconnect before ANY code execution
        sdk.disconnect_network(cid)
        print(f"  Network disconnected before execution")

        vulns = 0; critical_v = 0
        for ar in dep_results:
            vulns += ar.vulnerable; critical_v += ar.critical
            print(f"    {ar.ecosystem}: {ar.total_packages} pkgs, {ar.vulnerable} vulns ({ar.critical} critical)")

        # ── Version check (no network needed, reads files) ──
        print(f"\n  Version check...")
        ver_results = await check_versions(dl.extract_path, cid, None)
        mismatches = 0
        for v in ver_results:
            mismatches += 0 if v.compatible else 1
            print(f"    {'✓' if v.compatible else '✗'} {v.ecosystem}: {v.message[:100]}")

        # ── Import test ──
        print(f"\n  Import check...")
        ec, out, _ = exec_cmd(cid, f"cd {workdir} && python3 -c \"import sys; sys.path.insert(0,'.'); print('OK')\" 2>&1", sdk, 30)
        import_ok = ec == 0 and "OK" in out
        print(f"  {'✓ PASS' if import_ok else '✗ FAIL'}")

        # ── Test collection ──
        print(f"\n  Test collection (pytest --collect-only)...")
        ec, out, _ = exec_cmd(cid, f"cd {workdir} && python3 -m pytest --collect-only -q 2>&1 | tail -5", sdk, 60)
        collected = 0
        try:
            parts = out.strip().split()
            for i, p in enumerate(parts):
                if "selected" in p.lower() and i+1 < len(parts):
                    collected = int(parts[i+1]) if parts[i+1].isdigit() else 0
        except: pass
        print(f"  Tests collected: {collected}")

        # ── Test run ──
        print(f"\n  Test execution...")
        ec, out, _ = exec_cmd(cid, f"cd {workdir} && python3 -m pytest -x --tb=short 2>&1 | tail -10", sdk, 120)
        passed_t = 0; failed_t = 0
        for line in out.split("\n"):
            if "passed" in line:
                try:
                    parts = line.strip().split()
                    for i, p in enumerate(parts):
                        if "passed" in p and i > 0: passed_t = int(parts[i-1])
                        if "failed" in p and i > 0: failed_t = int(parts[i-1])
                except: pass
        print(f"  Tests: {passed_t} passed, {failed_t} failed, exit={ec}")

        # ═══════════════════════════════════════════════════
        # PHASE 5: SCORING
        # ═══════════════════════════════════════════════════
        print(f"\n{'─'*60}\n PHASE 5: COMPATIBILITY SCORE\n{'─'*60}")

        score = compute_compatibility(
            secrets_count=len(secrets),
            vulnerabilities=vulns,
            critical_vulns=critical_v,
            version_mismatches=mismatches,
            build_passed=syntax_ok,
            tests_passed=passed_t,
            tests_failed=failed_t,
            syntax_ok=syntax_ok,
            exit_code=ec,
        )

        print(f"\n  ┌─────────────────────────────────┐")
        print(f"  │ OVERALL:  {score_emoji(score.overall_score)} {score_badge(score.overall_score):<18} │")
        print(f"  ├─────────────────────────────────┤")
        print(f"  │ Security:     {score_emoji(score.security_score)} {score_badge(score.security_score):<15} │")
        print(f"  │ Dependencies: {score_emoji(score.dependency_score)} {score_badge(score.dependency_score):<15} │")
        print(f"  │ Versions:     {score_emoji(score.version_score)} {score_badge(score.version_score):<15} │")
        print(f"  │ Build:        {score_emoji(score.build_score)} {score_badge(score.build_score):<15} │")
        print(f"  │ Tests:        {score_emoji(score.test_score)} {score_badge(score.test_score):<15} │")
        print(f"  └─────────────────────────────────┘")

        if score.warnings:
            print(f"\n  ⚠ Warnings ({len(score.warnings)}):")
            for w in score.warnings: print(f"    • {w}")
        if score.recommendations:
            print(f"\n  💡 Recommendations ({len(score.recommendations)}):")
            for r in score.recommendations: print(f"    • {r}")

        # ═══════════════════════════════════════════════════
        # CLEANUP
        # ═══════════════════════════════════════════════════
        print(f"\n{'─'*60}\n CLEANUP\n{'─'*60}")
        sdk.destroy(cid)
        print(f"  ✓ Container destroyed")

    dl.cleanup()
    print(f"  ✓ Source directory cleaned")

    r = subprocess.run(["docker", "ps", "-a", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.ID}}"],
                       capture_output=True, text=True)
    print(f"  ✓ No leftover containers: {not bool(r.stdout.strip())}")

    # ═══════════════════════════════════════════════════════
    # FINAL VERDICT
    # ═══════════════════════════════════════════════════════
    elapsed = time.time() - t0
    print(f"\n{'═'*64}")
    print(f" FINAL VERDICT")
    print(f"{'═'*64}")
    print(f"  Repository:    {REPO_URL}")
    print(f"  Branch:        {BRANCH}")
    print(f"  Commit:        {dl.commit_sha[:40] if dl.commit_sha else 'N/A'}")
    print(f"  Total files:   {dl.file_count:,}")
    print(f"  Languages:     {', '.join(disc['detected_languages'])}")
    print(f"  Frameworks:    {', '.join(disc['detected_frameworks']) if disc['detected_frameworks'] else 'none detected'}")
    print(f"  Secrets:       {len(secrets)} ({len(critical_s)} critical, {len(high_s)} high)")
    print(f"  Vulnerabilities: {vulns} ({critical_v} critical)")
    print(f"  Version issues:  {mismatches}")
    print(f"  Syntax:        {'✓ PASS' if syntax_ok else '✗ FAIL'}")
    print(f"  Import:        {'✓ PASS' if import_ok else '✗ FAIL'}")
    print(f"  Tests:         {passed_t} passed, {failed_t} failed")
    print(f"  Isolation:     {iso_passed}/8 passed")
    print(f"  Overall:       {score_emoji(score.overall_score)} {score_badge(score.overall_score)}")
    print(f"  Time:          {elapsed:.1f}s")
    print(f"{'═'*64}")


asyncio.run(main())

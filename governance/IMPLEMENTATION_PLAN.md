# IMPLEMENTATION_PLAN — repofit build & certification

Waves with gates. A gate must pass before the next wave starts. If a gate cannot pass, report the exact blocker and stop — do not skip.

## Wave 1 — Deploy and verify the core stack

**Goal:** bring up the platform and prove the API runs against a real database.

1. `docker compose up -d` (db + api + web).
2. Verify `GET /api/v1/health → 200` and `GET /api/v1/readiness → 200`.
3. Verify Alembic migrations applied; confirm schema via direct DB query.
4. Run backend test suite: exact command + counts recorded.

**Gate 1:** live health 200 + DB migration applied + backend tests green. Evidence per `REPORT_SCHEMA.md`.

## Wave 2 — Prove the 5-phase verification pipeline end-to-end

**Goal:** run a real repository through the pipeline and get a scored verdict.

1. `run_full_pipeline.py` against a known target (e.g. a small public repo).
2. Confirm each phase executes: ingestion+discovery+secrets → static analysis → sandbox isolation (16/16) → dynamic eval (compile, dependency audit, version check, test run) → compatibility score.
3. Confirm sandbox profile is enforced (non-root, cap-drop ALL, read-only, network-none during execution).

**Gate 2:** a real compatibility report with per-axis scores + warnings/recommendations, backed by runtime output.

## Wave 3 — Wire the API to real stage evidence

**Goal:** close open item #2 — make `GET /compatibility/{job_id}` report actual findings, not hardcoded zeros.

1. Feed stage evidence (secrets count, vuln counts, version mismatches, build/test results) into `compute_compatibility` for API calls.
2. Persist evidence per stage; re-query via DB to confirm (not via API code inspection).

**Gate 3:** `GET /compatibility/{job_id}` returns non-trivial, evidence-derived scores that match a direct DB query.

## Wave 4 — Resolve version drift + harden

**Goal:** single source of version truth; close open item #1.

1. Reconcile `0.2.0` (pyproject) vs `0.3.0` (main.py). Pick one; update both `pyproject.toml` and the `/health` version string.
2. Confirm `GET /api/v1/health` returns the reconciled version.

**Gate 4:** version consistent across package metadata and runtime.

## Wave 5 — Certification & advisory report

**Goal:** produce the final certification report for repofit itself (self-hosting verification).

1. Run repofit's pipeline **against its own repository** (dogfood).
2. Emit the `REPORT_SCHEMA.md`-compliant certification report: four-axis verdict, score, restrictions vs blockers, provenance.

**Gate 5:** a `VERIFIED` (runtime-evidence-backed) certification report; remaining limitations logged as restrictions.

## Sequencing note

Waves are ordered by dependency: Wave 2 depends on Wave 1 (stack up), Wave 3 on Wave 2 (evidence exists), Wave 5 on Waves 3–4. Each wave is reported separately, per the wave structure in the `governed-platform-build` skill.

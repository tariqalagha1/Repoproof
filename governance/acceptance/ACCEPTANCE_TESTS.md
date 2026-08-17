# ACCEPTANCE_TESTS — repofit certification gates

Concrete, executable acceptance tests. Each maps to a gate in `IMPLEMENTATION_PLAN.md`. A gate is `PASS` only when every test in its set passes with **recorded runtime evidence**. No test here may be satisfied by documentation alone.

## Gate 1 — Core stack up

| # | Test | Command / probe | Pass criteria |
|---|---|---|---|
| 1.1 | API healthy | `curl -sf http://localhost:8000/api/v1/health` | HTTP 200, body `{"status":"healthy",...}` |
| 1.2 | API ready | `curl -sf http://localhost:8000/api/v1/readiness` | HTTP 200 |
| 1.3 | DB migrated | `docker compose exec db psql -U repoproof -d repoproof -c '\dt'` | expected tables present; alembic_version at head |
| 1.4 | Backend tests | `.venv/bin/pytest tests/ -v` (in `apps/api`) | collected/passed/failed recorded; 0 failed |
| 1.5 | Web up | `curl -sf http://localhost:3000` | HTTP 200 |

## Gate 2 — Pipeline end-to-end

| # | Test | Probe | Pass criteria |
|---|---|---|---|
| 2.1 | Phase 1 runs | `python3 run_full_pipeline.py` output | download + discovery + secrets scan lines present |
| 2.2 | Sandbox profile | `docker inspect <cid>` | non-root user, `Privileged=false`, `CapDrop=ALL`, `ReadonlyRootfs=true`, `NetworkMode=none` |
| 2.3 | Isolation tests | provision result | `isolation_tests_passed == isolation_tests_total == 16` |
| 2.4 | Dynamic eval | pipeline output | compile + dependency audit + version check + test run all present |
| 2.5 | Score emitted | pipeline output | overall + 5 axis scores with emoji/badge, warnings, recommendations |
| 2.6 | Cleanup | `docker ps -a --filter name=repoproof-full-pipeline` | no leftover container |

## Gate 3 — API score fed by real evidence

| # | Test | Probe | Pass criteria |
|---|---|---|---|
| 3.1 | Non-trivial score | `curl /api/v1/compatibility/{job_id}` | scores derived from persisted stage evidence, not hardcoded zeros |
| 3.2 | DB parity | direct SQL on stage/evidence tables | API response matches DB rows |

## Gate 4 — Version reconciled

| # | Test | Probe | Pass criteria |
|---|---|---|---|
| 4.1 | Single version | `pyproject.toml` vs `GET /health` | both report the same version |

## Gate 5 — Certification (dogfood)

| # | Test | Probe | Pass criteria |
|---|---|---|---|
| 5.1 | Self-scan | run pipeline against `tariqalagha1/repoproof-ai` | compatibility report produced |
| 5.2 | Report complete | report vs `REPORT_SCHEMA.md` | all required fields present |
| 5.3 | Verdict honest | four-axis block | no undifferentiated GO; restrictions vs blockers separated |
| 5.4 | Provenance | report provenance table | every claim `runtime_evidence` or `session_record` |

## Rules

- Record the exact command + output + timestamp for every test.
- A failed test fails the gate. Fix root cause, re-run the **whole** gate, not just the failing test.
- A test that cannot run because a real dependency is missing → gate is `HOLD`/`BLOCKED` with the blocker named, never a simulated pass.

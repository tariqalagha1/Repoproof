# BLUEPRINT — repofit architecture

Source: `apps/api/src/main.py`, `apps/api/src/domain/enums.py`, `apps/api/src/application/services/*`, `compose.yaml`, `README.md`.

## 1. System shape

```
                         ┌─────────────────────────────┐
   repo URL ───────────▶ │  FastAPI API  (apps/api)     │
                         │  SQLAlchemy + PostgreSQL     │
                         │  provider-neutral LLM layer  │
                         └──────────────┬──────────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              ▼                         ▼                         ▼
   ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
   │  Acquisition       │   │  Orchestration     │   │  Runner (Docker)   │
   │  safe zip download │   │  16-stage pipeline │   │  isolated sandbox  │
   │  + passive disc.   │   │  + plan + policy   │   │  + dependency/ver  │
   │  + secrets scan    │   │  + lifecycle       │   │  + test execution  │
   └────────────────────┘   └────────────────────┘   └────────────────────┘
                                        │
                                        ▼
                          ┌────────────────────────────┐
                          │  Compatibility Score       │
                          │  (GREEN/YELLOW/RED, 5 axes)│
                          └────────────────────────────┘
```

- **Backend:** FastAPI + SQLAlchemy (async) + PostgreSQL 16.
- **Frontend:** Next.js + TypeScript (`apps/web`).
- **Runner:** Docker-isolated execution (`infrastructure/docker/runner.Dockerfile`).
- **LLM:** provider-neutral abstraction (`infrastructure/llm/interface.py`) with `fake_provider` and `hermes_adapter`.

## 2. The 16-stage pipeline

Defined in `domain/enums.py` as `STAGE_DEFINITIONS`. Sequence is enforced by `STAGE_PREREQUISITES`.

| Seq | Stage | Criticality | Applicability |
|---|---|---|---|
| 00 | Intake | required | required |
| 01 | Passive Discovery | required | required |
| 02 | Plan Generation | required | required |
| 03 | Policy Validation | required | required |
| 04 | Environment Provisioning | required | required |
| 05 | Dependency Installation | required | required |
| 06 | Pre-Runtime Verification | required | required |
| 07 | Build | required | required |
| 08 | Infrastructure Startup | required | conditional |
| 09 | Application Startup | required | conditional |
| 10 | Live Workflow Testing | required | required |
| 11 | Architecture Portability | recommended | optional |
| 12 | Production Readiness | recommended | optional |
| 13 | Output Correctness | recommended | required |
| 14 | Compliance | optional | optional |
| 15 | Final Advisory Report | required | required |

`skipped_not_applicable` is a valid stage status — conditional/optional stages may be skipped with reason, but **required** stages may not.

## 3. Domain model (entities)

- **Project** — top-level container (`org_id`, name, description).
- **Repository Connection** — a validated, normalized repo URL bound to a project (`status`: submitted → valid/invalid/discovered/error).
- **Master Verification Job** — one end-to-end verification run against a repo+branch; owns the 16 stages.
- **Stage** — one pipeline step (`StageType`, `StageStatus`, criticality, applicability).
- **Manifest / Discovery Claims / Discovery Warnings** — passive-discovery output.
- **Plan** — generated execution plan: stages + commands + conflicts (`Ecosystem`: python/node/rust/go/java/dotnet/ruby/php/unknown).
- **Policy Validation Result** — policy verdict against the plan (`PolicyOutcome`).
- **Runner Environment** — the provisioned sandbox with security profile, resource limits, network policy, source attachment.
- **Run / Transition** — legacy project-scoped run with a lifecycle state machine.

## 4. Sandbox security profile (non-negotiable defaults)

From `main.py` `provision_environment` and `run_full_pipeline.py`:

```
--user 1000:1000
--security-opt no-new-privileges:true
--cap-drop ALL
--read-only
--tmpfs /tmp:exec,size=128M
--tmpfs /workspace:exec,size=1G
--memory 512m --memory-swap 512m
--cpu-shares 512
--pids-limit 64
--network none
--init
```

Isolation is validated: `isolation_tests_passed=16, isolation_tests_total=16`. Source is attached read-only (`verified_read_only: true`); network is `default_deny` and only re-connected for dependency installation, then disconnected again.

## 5. API surface (v0.3.0)

Base prefix `/api/v1`. Key routes:
- `GET /health`, `/readiness`, `/llm/status`
- `POST|GET /projects`, `GET /projects/{id}`
- `POST|GET /repository-connections`
- `POST|GET /master-jobs`, `GET /master-jobs/{id}/stages|progress|manifest`, `POST /master-jobs/{id}/complete-intake|pause|resume|cancel`
- `POST /master-jobs/{id}/discover`, `/generate-plan`, `/validate-policy`
- `GET|POST /environments/*` (provision, security-profile, resource-limits, network-policy, source-attachment, cancel)
- `GET /compatibility/{job_id}`
- `POST|GET /projects/{id}/runs`, `POST /runs/{id}/transitions`

## 6. Tech-stack summary

| Layer | Stack |
|---|---|
| API | Python ≥3.11, FastAPI ≥0.115, SQLAlchemy ≥2.0 (async), asyncpg, Alembic, pydantic-settings |
| Frontend | Next.js + TypeScript |
| DB | PostgreSQL 16 (prod), aiosqlite (pipeline scripts) |
| Runner | Docker SDK + subprocess fallback |
| LLM | fake / hermes adapter (provider-neutral) |

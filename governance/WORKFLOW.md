# WORKFLOW — how a verification job flows

Source: `domain/enums.py` (`RunLifecycle`, `ALLOWED_TRANSITIONS`, `StageType`, `StageStatus`), `main.py` routes.

## 1. Lifecycle state machine

A verification run moves through states only along allowed transitions (`ALLOWED_TRANSITIONS`). Illegal transitions raise `InvalidTransitionError` — they are refused, not coerced.

```
created → discovering → plan_ready → awaiting_approval → approved
        → provisioning → executing → verifying → reporting → completed
```

Terminal / side states: `completed`, `cancelled`. Recoverable states: `failed`, `blocked`, `partial`.

Key transition rules:
- `awaiting_approval` → `approved` is the only exit (plus fail/cancel). There is no auto-approve.
- `blocked` may re-enter `discovering` (re-run after unblock) or go to `failed`/`cancelled`.
- `failed` may re-enter `discovering` (retry from discovery), never jump straight to `executing`.
- `completed` and `cancelled` are terminal (`set()`).
- `partial` may be promoted to `completed` or re-run from `discovering`.

## 2. The 16 stages in sequence

Stage prerequisites are enforced (`STAGE_PREREQUISITES`). Each stage is in one of: `pending → ready → running → completed` (or `completed_with_findings`, `failed`, `blocked`, `skipped_not_applicable`, `cancelled`, `paused`).

```
00 intake ─▶ 01 passive_discovery ─▶ 02 plan_generation ─▶ 03 policy_validation
  ─▶ 04 environment_provisioning ─▶ 05 dependency_installation
  ─▶ 06 pre_runtime_verification ─▶ 07 build
  ─▶ 08 infrastructure_startup ─▶ 09 application_startup
  ─▶ 10 live_workflow_testing
  ─▶ (11 architecture_portability | 12 production_readiness | 13 output_correctness | 14 compliance)
  ─▶ 15 final_advisory_report
```

Stages 08/09 are `conditional`; 11/12/14 are `optional`; 13 is `required` but `recommended` criticality; 00–07, 10, 15 are `required`.

## 3. Gate mechanics

- **Intake gate (00):** repo URL validated and normalized (`.git` suffix stripped, trailing slash removed); branch + commit hash captured.
- **Approval gate (03→04):** policy validation must return an outcome before provisioning. `approved_with_restrictions` is the expected "go with caveats" verdict — restrictions travel with the job, not silently dropped.
- **Provisioning gate (04):** sandbox must be provisioned with the full security profile (non-root, cap-drop ALL, read-only root, `--network none`) and isolation tests passing (16/16).
- **Network gate (05):** network is connected **only** for dependency installation, then disconnected before execution.
- **Live-test gate (10):** actual workflow exercised against live infrastructure, not mocked.
- **Final gate (15):** advisory report emitted with score + warnings + recommendations.

## 4. Job control endpoints

`complete-intake`, `pause`, `resume`, `cancel` are explicit transitions on a master job. Pausing freezes the job; resume continues from the same stage; cancel is terminal.

## 5. Who/what moves between stages

- **Deterministic steps** (URL validation, normalization, compile, dependency audit, version check) run without LLM.
- **LLM-assisted steps** (plan generation, advisory wording) are provider-neutral and flagged by `CommandSource` (`llm` / `deterministic` / `manual` / `fallback`).
- **Approval** is a human/principal decision point, never auto-granted.

## 6. Progress

`GET /master-jobs/{id}/progress` returns `compute_progress(...)` over stage statuses. Progress is derived from stage completion, not from elapsed time or agent self-report.

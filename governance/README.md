# repofit — RepoProof AI

**Codename:** `repofit`
**Source repository:** https://github.com/tariqalagha1/Repoproof
**Product:** Automated software repository verification — evidence-backed verification gates, capability/risk identification, controlled upgrade recommendations.

repofit answers one question for any software repository: **"is this repo fit to trust and deploy?"** — and produces a scored, evidence-backed verdict rather than an opinion.

## What this directory is

This is the governance and delivery scaffold for repofit. The code lives in the source repo; **this directory defines how the project is governed, decided, scored, and certified.** Nothing here is decorative — every file is a working contract that build agents and reviewers are expected to follow.

## Document map

| File | Purpose | Consult when |
|---|---|---|
| `README.md` | This map | onboarding |
| `BLUEPRINT.md` | System architecture: components, 16-stage pipeline, data model, sandbox profile | building or changing the platform |
| `CONSTITUTION.md` | Non-negotiable principles (evidence-before-claims, no fabrication, honest HOLD) | any certification claim or gate decision |
| `WORKFLOW.md` | How work flows: lifecycle state machine, gate mechanics, transitions | running or reviewing a verification job |
| `DECISION_RULES.md` | Four-axis decision model + policy rules (allow/deny/warn/approval) | a gate needs a verdict |
| `SCORING.md` | Compatibility scoring rubric (GREEN/YELLOW/RED, 5 axes, exact thresholds) | interpreting or emitting a score |
| `REPORT_SCHEMA.md` | Certification report schema — the exact fields every report must carry | producing or auditing a report |
| `PROJECT_REGISTRY.md` | Registry of all projects under ai-enterprise-os | portfolio status |
| `IMPLEMENTATION_PLAN.md` | Phased build plan with gates | sequencing work |
| `acceptance/ACCEPTANCE_TESTS.md` | Acceptance test suite: exact commands, pass/fail, evidence required | certifying a gate |

## Ground truth

The contents of this scaffold were authored against the **actual codebase** (cloned 2026-08-17), not the README alone. Stage definitions, lifecycle transitions, policy enums, scoring thresholds, and the Docker sandbox profile below are transcribed from `apps/api/src/` — see each document's "Source" line for the originating file.

## Known version drift (as of 2026-08-17)

- `apps/api/pyproject.toml` declares `0.2.0`; `apps/api/src/main.py` serves `version = "0.3.0"` at `/api/v1/health`.
- This is recorded as an open reconciliation item, not silently resolved. See `PROJECT_REGISTRY.md`.

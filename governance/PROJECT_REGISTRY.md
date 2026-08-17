# PROJECT_REGISTRY — ai-enterprise-os

Single source of truth for every project under the `ai-enterprise-os` umbrella. Each entry records identity, status, provenance, and open reconciliation items.

## Format

```
- codename (product name)
  source: <repo url>
  status: <NOT_STARTED | IN_PROGRESS | BLOCKED | COMPLETED[VERIFIED|UNVERIFIED|CLAIMED]>
  stack: <primary stack>
  pipeline: <current stage / phase>
  provenance: <runtime_evidence | session_record | memory_claim | inference | unset>
  open_items: <reconciliation / blocker list>
```

## Entries

### repofit (RepoProof AI)

- **source:** https://github.com/tariqalagha1/repoproof-ai
- **status:** `NOT_STARTED` (registered to portfolio; governance scaffold authored; no runtime build/verification yet)
- **stack:** Python ≥3.11 · FastAPI · SQLAlchemy(async) · PostgreSQL 16 · Next.js/TypeScript · Docker runner · provider-neutral LLM (fake + hermes adapter)
- **pipeline:** 16-stage (00–15); all stages defined, none executed against a real target yet
- **provenance:** `runtime_evidence` (cloned 2026-08-17; README, compose.yaml, `main.py`, `domain/enums.py`, `domain/policy_enums.py`, `compatibility_scorer.py` read directly)
- **governance dir:** `/opt/ai-enterprise-os/projects/repofit/`
- **open_items:**
  1. Version drift — `pyproject.toml` = `0.2.0`, `main.py` serves `0.3.0`. Reconcile to a single version.
  2. `main.py` `get_compatibility` hardcodes `secrets=0`, `vulnerabilities=0`, `version_mismatches=0` for API calls (score is not yet fed from real stage evidence). Real scoring currently only runs in `run_full_pipeline.py`.
  3. No runtime deployment executed yet — no live `docker compose up`, no verification run against a target repo.

## Rules

- New projects are added here at **start of work**, not retroactively.
- Status changes only via evidence: `IN_PROGRESS` on real work starting, `COMPLETED/VERIFIED` only with runtime evidence.
- This registry is a governance document; the Hermes Chief-of-Staff registry (`~/.hermes/chief-of-staff/registry.json`) is the portfolio control layer. Keep both consistent.

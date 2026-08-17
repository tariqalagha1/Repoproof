# DECISION_RULES — verdicts and policy

Source: `domain/policy_enums.py`, `domain/enums.py`, `main.py` `validate-policy`.

## 1. Four-axis decision model

No undifferentiated GO. Every gate verdict is reported on four separated axes:

| Axis | Vocab | Applies to |
|---|---|---|
| **Verification (scientific analog)** | `ADVANCE` / `REVISE` / `HOLD` / `TERMINATE` | evidence quality of the verification engine's findings |
| **Clinical** | `CLINICAL_DEPLOYMENT_HOLD` | **N/A for repofit** — no clinical claims; axis explicitly marked not-applicable rather than copied in |
| **Commercial** | `COMMERCIAL_ASSET_REVISE` | pricing, packaging, productization of the verification service |
| **Platform** | `SYSTEM_VERTICAL_CERTIFIED_WITH_RESTRICTIONS` | engineering certification of the platform itself |

Example verdict — a repo scan that passed all checks but was verified by only one provider:

```
Verification: ADVANCE (evidence-backed, single-provider)
Clinical:      N/A
Commercial:    COMMERCIAL_ASSET_REVISE (no pricing model yet)
Platform:      CERTIFIED_WITH_RESTRICTIONS (single-provider review = restriction, not a hold)
```

## 2. Policy decision vocabulary

`PolicyDecision`: `allow` | `deny` | `warn` | `require_approval` | `not_applicable`
`PolicyOutcome`: `pass` | `fail` | `warn` | `error` | `skipped`
`RiskLevel`: `none` | `low` | `medium` | `high` | `critical`
`RestrictionType`: `network` | `filesystem` | `capability` | `resource` | `timeout` | `execution`
`ApprovalScope`: `single_run` | `master_job` | `project` | `global`
`PolicyArea`: `security` | `compliance` | `operational` | `quality` | `architecture`

## 3. Decision rules

1. **Any `critical` risk → `deny` (or `HOLD` + exact blocker).** e.g. hardcoded secrets present, critical vuln in deps.
2. **`high` risk → `require_approval`**, scoped to the narrowest `ApprovalScope` that suffices (`single_run` preferred over `global`).
3. **`medium`/`low` → `warn`** with the finding recorded; does not block provisioning but appears in the final report.
4. **Unavailable real dependency (no key, no browser, geo-block) → `HOLD`**, never a simulated pass.
5. **Non-blocking limitations → restrictions**, not gates. Record them; continue product work. Examples: single-provider review, no external domain-validator, surrogate endpoint.
6. **Restrictions travel with the job.** A verdict of `approved_with_restrictions` must carry the restriction list into downstream stages and the final report — never silently dropped.
7. **`require_approval` cannot be self-satisfied** by the agent that raised it. The principal or a separate verifier approves.

## 4. Hard blocks (only these halt product work)

- Data loss
- Tenant isolation breach
- Secret leakage
- Lifecycle-integrity violation
- Fabricated evidence
- Unsupported clinical/scientific claims (N/A axis for repofit, but reserved)

## 5. Restriction vs. block — quick test

Ask: "Does this prevent the platform from working, or does it just qualify the confidence of the result?" If it qualifies confidence → **restriction**. If it corrupts data/isolates tenants/leaks secrets → **block**.

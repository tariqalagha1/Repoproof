# SCORING — compatibility rubric

Source: `application/services/compatibility_scorer.py` (transcribed exact thresholds).

## 1. Scale

`Score` = `GREEN` (safe) | `YELLOW` (caution) | `RED` (unsafe).

| Badge | Emoji | Meaning |
|---|---|---|
| ✅ SAFE | 🟢 | all checks pass |
| ⚠️ CAUTION | 🟡 | some issues found |
| 🚫 UNSAFE | 🔴 | critical issues |

## 2. Five axes and exact thresholds

### Security (`security_score`)
- `RED` if `secrets_count > 0` — warning "N hardcoded secrets found"; recommend env vars / secrets manager.
- else `GREEN`.

### Dependencies (`dependency_score`)
- `RED` if `critical_vulns > 0` — "update immediately".
- `YELLOW` if `vulnerabilities > 5` — "review and update".
- `YELLOW` if `0 < vulnerabilities <= 5` — "low-severity vulnerabilities".
- else `GREEN`.

### Versions (`version_score`)
- `YELLOW` if `version_mismatches > 0` — "align runtime versions with repository requirements".
- else `GREEN`.

### Build (`build_score`)
- `RED` if `not syntax_ok` — "syntax errors in source".
- `GREEN` if `build_passed`.
- else `YELLOW`.

### Tests (`test_score`)
- `RED` if `tests_failed > 0 and tests_passed == 0`.
- `YELLOW` if `tests_failed > 0` (some passed).
- `GREEN` if `tests_passed > 0`.
- `YELLOW` if no tests at all (0/0) — unverified, not safe.

## 3. Overall score

**Worst of all five axes.** If any axis is `RED`, overall is `RED`; else if any `YELLOW`, overall is `YELLOW`; else `GREEN`. One critical finding sinks the whole verdict.

## 4. Report output fields

`CompatibilityReport` carries, in addition to the five scores: `secrets_found`, `vulnerabilities`, `critical_vulns`, `version_mismatches`, `build_passed`, `tests_passed`, `tests_failed`, plus `warnings[]` and `recommendations[]`.

## 5. Worked examples

**A — clean repo (0 secrets, 0 vulns, 0 mismatches, build ok, 20/0 tests):**
security 🟢 · deps 🟢 · versions 🟢 · build 🟢 · tests 🟢 → **overall 🟢 ✅ SAFE**

**B — one hardcoded secret, 3 low vulns, build ok, 0/0 tests:**
security 🔴 · deps 🟡 · versions 🟢 · build 🟢 · tests 🟡 → **overall 🔴 🚫 UNSAFE** (secret alone is fatal; no tests keeps tests at YELLOW)

**C — 6 vulns, 1 version mismatch, build ok, 5 passed / 1 failed:**
security 🟢 · deps 🟡 · versions 🟡 · build 🟢 · tests 🟡 → **overall 🟡 ⚠️ CAUTION**

## 6. Scoring integrity rules

- Thresholds above are the source of truth. Do not "round up" a YELLOW to GREEN.
- Every `RED` must carry a corresponding warning + recommendation.
- A 0/0 test result is `YELLOW` (unverified), never `GREEN` — absence of tests is not proof of correctness.

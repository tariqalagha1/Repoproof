# REPORT_SCHEMA — certification report format

Every certification report for repofit must carry all of the following. Missing fields → the report is `UNVERIFIED`, not `VERIFIED`.

## 1. Required fields

### Identity
- `project` (codename + source repo URL)
- `commit_sha` / `branch` under verification
- `timestamp` (ISO-8601 UTC)
- `reporter` (agent or verifier)

### Execution evidence (exact, not paraphrased)
- Exact test command (e.g. `.venv/bin/pytest tests/ -v`)
- Collected / passed / failed / skipped counts
- Execution duration
- Failing test names (if any)
- Exact API routes verified, with status codes (e.g. `GET /api/v1/health → 200`)
- Database migration revision applied
- Running service health status (live check, not the YAML definition)

### Decision
- Four-axis verdict (see `DECISION_RULES.md`), one line per axis:
  - Verification: `ADVANCE` / `REVISE` / `HOLD` / `TERMINATE`
  - Clinical: `N/A` (repofit)
  - Commercial: `COMMERCIAL_ASSET_REVISE` / status
  - Platform: `SYSTEM_VERTICAL_CERTIFIED_WITH_RESTRICTIONS` / status
- `completion` marker: `VERIFIED` / `UNVERIFIED` / `CLAIMED` (default `UNVERIFIED`)

### Score
- `overall` + five axes (`security`, `dependencies`, `versions`, `build`, `tests`), each `GREEN`/`YELLOW`/`RED` + emoji + badge
- `warnings[]`, `recommendations[]`

### Honest limitations
- Unresolved limitations stated plainly, classified as **restriction** vs **blocker** (per `DECISION_RULES.md` §5)
- Provenance of every claim (`runtime_evidence` / `session_record` / `memory_claim` / `inference`)

## 2. What is NOT a valid report

- A report that lists file/table/endpoint counts as proof of function (operational evidence only).
- A report with a `VERIFIED` completion but no test command or no live health check.
- A report asserting percentages or pass counts that were never observed.
- A report that says "complete" while the test suite shows failures.

## 3. Report ordering

1. Verdict summary (four axes + completion marker + score)
2. Execution evidence (commands, counts, status codes)
3. Score breakdown
4. Warnings + recommendations
5. Restrictions vs blockers
6. Provenance

## 4. Provenance table

| source_type | authoritative? | example |
|---|---|---|
| `runtime_evidence` | yes | a DB row queried, an HTTP 200, a re-read file |
| `session_record` | yes | recorded session output |
| `memory_claim` | no | "I remember it worked" |
| `inference` | no | deduced, not observed |
| `unset` | no | missing |

# PREMORTEM output template

The skill writes one file per run to `.premortems/PREMORTEM-<ISO8601>.md` using this
exact structure. The frontmatter is the machine-readable contract consumed by
`scripts/sarif_export.py` and by CI — do not rename or drop fields.

`Location` MUST be `file:line` or `file:start-end` (e.g. `src/engine.py:88-115`). A
prose location ("section 5") is invalid: the SARIF exporter warns and defaults it to
line 1, losing the clickable anchor. Severity is `high|medium|low`; Confidence is
`confirmed|likely|speculative`.

For a **plan/spec pre-mortem** (`scope: plan`), `Location` is `file:§section` (e.g.
`plan.md:§T3`) and SARIF export does not apply — the markdown report is the deliverable.

---

```markdown
---
generated: <ISO8601 UTC, e.g. 2026-06-19T14:30:00Z>
skill: premortem-code
mode: <quick|standard|deep>
target: <pr/branch/commit/working-tree identifier>
scope: <pr|branch|commit|working-tree|plan>
stack_detected: [<e.g. python-fastapi, postgres>]
addenda_loaded: [<e.g. stack-python-fastapi.md, stack-postgres.md>]
verdict: <GO|REFINE|REWORK|ABANDON>
risk_counts:
  high: <int>
  medium: <int>
  low: <int>
dropped_findings_count: <int>
---

## Detailed findings

### Finding 1: <short incident title>

**Category:** <one of the 10 catalogue categories, or a stack-extended one>
**Severity:** <high|medium|low>
**Confidence:** <confirmed|likely|speculative>
**Location:** `<file>:<line>` or `<file>:<start>-<end>`
**Mitigation verified absent:** <the guard/validation/lock that should exist and the
cited evidence it does not — e.g. "no lock around the check-then-act at
worker.py:142-150; grep for 'Lock(' in worker.py → 0 matches">

#### Failure narrative
<past-tense account of the incident as if it already happened: what was observed,
the plausible future edit that triggered it, why the fragility let it through, and how
(or whether) it would be caught>

**Hardening:** <1–3 concrete, implementable suggestions — optional but recommended;
this extends the original contract (R1-PRC014) without removing any field>

### Finding 2: <...>
<...>

## Dropped findings (for transparency)

<findings considered but discarded by the verification protocol, each with the gate
that failed — e.g. "Suspected race in cache.py:30 — DROPPED at Evidence gate: a lock
IS present at cache.py:24">
```

---

Notes for the exporter (`sarif_export.py`):
- `risk_counts` drives the PR-comment table and must equal the number of findings at
  each severity in "Detailed findings" (Dropped findings are NOT counted).
- SARIF `message.text` = the finding title + the first line of its Failure narrative.
- SARIF `result.level`: high→error, medium→warning, low→note.

Format conceptually adapted (MIT) from honnibal/claude-skills "Output File Structure";
frontmatter fields mirror the user's original contract (`.research/ORIGINAL-output-contract.md`).

# Verification Protocol (anti-false-positive)

Load this before reporting ANY finding. Its job is to stop plausible-but-wrong
findings from reaching the report, and to make Severity, Confidence, and the final
verdict reproducible across runs. A finding that fails a gate is **omitted**,
**downgraded**, or **rephrased as a question** — never shipped as a soft accusation.
Anything the protocol discards goes in the "Dropped findings" section for transparency.

## Hard gates (apply in order, once per finding)

| # | Gate | Pass condition (objective) |
|---|---|---|
| 1 | **Anchor** | You read the whole enclosing symbol/module, not just the diff hunk, and can state `file:start-end`. (Plan/spec mode: read the whole plan and cite `file:§section`.) |
| 2 | **Evidence** | The mitigation that *should* exist is provably absent: a `file:line` citation, pasted tool output, or an explicit "0 matches" after a repo search — not "I looked". (Plan/spec mode: quote the exact plan text — the missing, contradictory, or unverifiable line, or "no task covers X".) |
| 3 | **Severity** | Assigned per the scale in `fragility-catalog-core.md` (high/medium/low), honestly. |
| 4 | **Confidence** | Assigned per the rule below (`confirmed`/`likely`/`speculative`). |
| 5 | **Format** | The finding has Category, Severity, Confidence, `Location` as `file:line`/`file:start-end` (or `file:§section` in plan/spec mode), `Mitigation verified absent`, and a Failure narrative. |

If gate 1 or 2 fails → the finding is `speculative` at best; usually Drop it.

## Confidence assignment (gate 4 — R2-PRC001)

- `confirmed` — gate 2 passed with a concrete `file:line` (or `file:§section` in plan/spec
  mode) showing the guard/step is absent or contradicted. Only `confirmed` findings can
  drive an `ABANDON` verdict.
- `likely` — strong indication, but no exact anchor (e.g. the pattern is present but
  you could not pin the precise missing line).
- `speculative` — plausible but unverified. Default to **Dropped** unless it is a
  high-impact hypothesis worth surfacing explicitly as a question.

## Verification by issue type (what "evidence" means)

- **Concurrency / non-atomic (cat 6):** show there is no lock/transaction/idempotency
  guarding the check-then-act, and name the two interleaving paths.
- **Data assumptions (cat 4) / invariants (cat 7):** show the boundary/validation is
  absent at the point the data enters, and the consumer that assumes it.
- **Stringly-typed (cat 3):** show the producer and consumer of the string and that no
  shared enum/constant binds them.
- **Resource lifecycle (cat 9):** show an exit path (early return/raise) that skips
  cleanup.
- **Version-coupled (cat 10):** name the undocumented behaviour and the dependency
  whose upgrade would break it.

## Do NOT flag

- Current, real bugs → tell the user separately; not a pre-mortem finding.
- Style, naming, formatting, "could be more detailed", missing tests as such.
- Adversarial scenarios (a developer deliberately sabotaging the code).
- Edits so large they amount to a rewrite.
- Anything you cannot anchor to `file:line` AND cannot phrase as a concrete future
  change → Drop it.

## Verdict calibration (one worked example each — R1-PRC008)

The verdict rubric (operational definitions in `SKILL.md`) keys on Severity, Confidence,
and structural-vs-local. Examples so two runs converge:

- **GO** — Only a `low` finding: an uncommon error path logs but does not handle a
  `None`, failing loudly. Nothing blocking. Track for follow-up.
- **REFINE** — A `high` finding that is **local**: a function assumes a non-empty list
  (cat 4); the fix is one guard at the top of that single function. Mergeable after the
  guard is added.
- **REWORK** — A `high` **structural** finding: check-then-act on a shared counter
  across two handlers (cat 6); the fix needs a lock or a redesign touching >1 module.
  Do not merge as-is.
- **ABANDON** — The change's stated premise is contradicted by a `confirmed` finding:
  the PR claims "this migration is idempotent", but there is a confirmed `file:line`
  showing a second run double-applies. Reconsider the change.

The no-self-grading idea and the pre-registered decision-rule are conceptually adapted
(Apache-2.0) from boshu2/agentops; see `CREDITS.md`.

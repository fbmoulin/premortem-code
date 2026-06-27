# Plan/Spec Failure Catalogue

The failure-mode catalogue for the **plan/spec pre-mortem mode**. Load this *instead of* the
stack addenda when the target is a plan or spec document (not a code diff). It is the analogue of
`fragility-catalog-core.md`, but the failures are about **executing a plan**, not running code.

A plan pre-mortem is **not a proofread** and **not a wishlist**. Assume the plan was followed by a
competent engineer and the execution **still failed or went off the rails** — then find the place in
the plan that allowed it. For each category ask: *"a diligent executor follows this step exactly — what
breaks, stalls, or silently does the wrong thing, and why didn't the plan catch it?"*

## Contents

- [Calibration rules](#calibration-rules-apply-to-every-finding)
- [Severity & Confidence](#severity--confidence)
- [What "evidence" means for a plan](#what-evidence-means-for-a-plan)
- The 10 categories:
  1. [Non-falsifiable acceptance criteria](#1-non-falsifiable-acceptance-criteria)
  2. [Undeclared premise](#2-undeclared-premise)
  3. [Task ordering & dependency gaps](#3-task-ordering--dependency-gaps)
  4. [Missing rollback / idempotency](#4-missing-rollback--idempotency)
  5. [Under-scoped task hiding a rewrite](#5-under-scoped-task-hiding-a-rewrite)
  6. [Vague or unverifiable step](#6-vague-or-unverifiable-step)
  7. [No verification seam](#7-no-verification-seam)
  8. [Contract drift between tasks](#8-contract-drift-between-tasks)
  9. [Unstated resource / permission / secret](#9-unstated-resource--permission--secret)
  10. [Premise contradicted by reality](#10-premise-contradicted-by-reality)

## Calibration rules (apply to every finding)

1. **Execution failure, not authorship nitpick.** Wrong word choice or formatting is not a finding;
   a step that *leads a correct executor to a wrong/broken outcome* is.
2. **Plausible, not pathological.** Assume a competent, well-intentioned executor. "If they ignored
   the plan" is not a finding.
3. **Specific, anchored to a task/section.** Name the task or heading (`plan.md:§T3`), not "the plan
   is vague" in the abstract.
4. **Pre-execution.** The flaw must be visible in the plan *before* running it — that is the point.
5. **Honest severity.** Not every gap blocks execution.

## Severity & Confidence

Reuse the scales from `fragility-catalog-core.md`:
- **Severity** `high|medium|low` — `high` = the plan, followed faithfully, produces a broken/incorrect
  result or a stuck execution that no step would catch.
- **Confidence** `confirmed|likely|speculative` — `confirmed` quotes the exact plan text (or its
  absence) that proves the flaw. Only `confirmed` can drive `ABANDON`.

## What "evidence" means for a plan

Gate 2 (Evidence) is satisfied by **quoting the plan**: the line/section that is missing, contradictory,
or unverifiable — or an explicit "no task covers X" after reading the whole plan. Not "feels thin".

---

## The 10 categories

### 1. Non-falsifiable acceptance criteria
A "done" condition you cannot objectively check: "works well", "is robust", "handles load". The executor
cannot tell done from not-done, so the task is declared complete on vibes. Prefer criteria a script or a
named observation can verify.

### 2. Undeclared premise
The plan silently assumes a service exists, a data shape, an API contract, a permission, or prior state —
without stating or verifying it. If the assumption is false, the task collapses mid-execution. Name the
assumed fact and the task that rides on it.

### 3. Task ordering & dependency gaps
Task N consumes an artifact task M produces, but the order/handoff is not pinned; or two "parallel" tasks
mutate the same file/resource. Execution interleaves wrong and one task clobbers another's precondition.

### 4. Missing rollback / idempotency
A step mutates durable state (migration, deploy, bulk edit, data backfill) with no re-run safety and no
undo. A retry after a partial failure double-applies or corrupts. The plan needs an idempotency or
rollback step and has none.

### 5. Under-scoped task hiding a rewrite
A single "bite-sized" task ("update the auth flow", "swap the cache") that actually requires redesigning
multiple modules or a public contract. The plan treats a structural change as a local one, so the
estimate and the seams are wrong.

### 6. Vague or unverifiable step
"Handle errors", "optimize the query", "make it scale" with no concrete definition, target, or check.
The executor guesses; two runs diverge. Pin the exact behaviour and how it's confirmed.

### 7. No verification seam
A high-risk task with no test, validation, or observation step — success is asserted, not checked. Pairs
with `verification-before-completion`: every risky task should end in evidence, not a claim.

### 8. Contract drift between tasks
Task A's output format/shape ≠ task B's assumed input; a stringly-typed handoff ("pass the config")
that the two tasks interpret differently. The seam compiles in prose but breaks at execution.

### 9. Unstated resource / permission / secret
The plan needs a token, env var, network egress, CI scope, or credential that is never called out.
Execution blocks halfway, or someone improvises an insecure shortcut to get unblocked.

### 10. Premise contradicted by reality
A declared goal conflicts with a constraint already known: "zero downtime" but a step takes an exclusive
lock; "no breaking changes" but a task renames a public field. A `confirmed` finding here is `ABANDON`
territory — the plan's stated premise cannot hold.

---

Categories adapted from general plan/project pre-mortem practice (Klein) and this skill's own
code fragility catalogue; the verdict ladder mirrors `SKILL.md`.

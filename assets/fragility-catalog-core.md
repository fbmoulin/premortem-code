# Fragility Catalogue (core)

The universal failure-mode catalogue for `premortem-code`. Stack addenda
(`stack-*.md`) extend these categories with technology-specific patterns; this
file is the always-loaded baseline. Read it before scoring any finding.

A pre-mortem is **not a bug hunt**. The code may be correct today. You are looking
for places where a *plausible future edit* — the kind a competent developer would
make during a normal change — would break something in a non-obvious way. For each
category, the question is always: *"what reasonable change here breaks this, and how
does the breakage stay hidden?"*

## Contents

- [Calibration rules](#calibration-rules-apply-to-every-finding)
- [Severity scale](#severity-scale-exactly-three-levels--no-critical)
- [Confidence](#confidence-used-by-the-verdict-rubric)
- The 10 categories:
  1. [Implicit ordering dependencies](#1-implicit-ordering-dependencies)
  2. [Coupling through shared mutable state](#2-coupling-through-shared-mutable-state)
  3. [Stringly-typed contracts](#3-stringly-typed-contracts)
  4. [Assumptions baked into data transformations](#4-assumptions-baked-into-data-transformations)
  5. [Coincidental correctness](#5-coincidental-correctness)
  6. [Non-atomic compound operations](#6-non-atomic-compound-operations)
  7. [Invisible invariants](#7-invisible-invariants)
  8. [Load-bearing defaults](#8-load-bearing-defaults)
  9. [Implicit resource lifecycle](#9-implicit-resource-lifecycle)
  10. [Version-coupled assumptions](#10-version-coupled-assumptions)

## Calibration rules (apply to every finding)

1. **Not a current bug.** If something is broken *today*, that is a separate report
   to the user, not a pre-mortem finding.
2. **Plausible edits only.** The imagined change must have a believable motivation
   (feature, refactor, perf, dependency bump) and pass code review. "If someone
   rewrote it entirely" is not a finding.
3. **Specific, not generic.** Name the actual function, variable, file, and line.
   "This has no tests" is an observation, not a finding.
4. **Cause and effect non-obvious.** Prefer cases where the change is in one place
   and the breakage surfaces elsewhere, or only under load / specific input.
5. **Honest severity** (see scale below). Not everything is `high`.

## Severity scale (exactly three levels — no "critical")

- `high` — silent data loss/corruption, security exposure, or an outage-class failure
  that no test would catch. A source-catalogue "Critical" maps here.
- `medium` — a clear failure in a real code path; recoverable or loud, but costly.
- `low` — a failure confined to an uncommon path, or one that fails loudly and early.

## Confidence (used by the verdict rubric)

- `confirmed` — you cited `file:line` evidence that the guarding mitigation is absent.
- `likely` — strong indication but no exact anchor.
- `speculative` — plausible but unverified (usually belongs in Dropped findings).

---

## The 10 categories

### 1. Implicit ordering dependencies
Code that must run in a particular order but does not enforce it: setup that must
precede use, processing that assumes inputs arrive sorted, init steps where step 3
silently relies on step 1.
**Future edit:** someone reorders calls, inserts a step between two others, or uses
an object before it is fully initialised.
**Hardening:** assert the precondition at entry; make the dependency explicit in the
type/constructor; fail loudly if used out of order.

### 2. Coupling through shared mutable state
Two components that talk through a shared object (dict, list, module global, an
attribute on a passed-in object) instead of explicit arguments and returns. A reader
of one side may not see that the other reads/writes the same state.
**Future edit:** someone changes one side's use of the state, or adds caching that
freezes a value the other side expected to keep changing.
**Hardening:** pass data explicitly; make the shared object immutable or copy-on-read;
document the contract at the mutation site.

### 3. Stringly-typed contracts
Logic that depends on exact string values — dict keys, status fields, format strings,
column names, error-message matching. No type checker or test enforces these.
**Future edit:** someone renames a status, adds an enum variant the existing
if/elif/match does not handle, or changes a key in one place but not another.
**Hardening:** replace magic strings with enums/constants/typed records; add an
exhaustiveness check (match without a catch-all, or an explicit unreachable assert).

### 4. Assumptions baked into data transformations
A function that assumes a shape/range/distribution: non-empty list, positive value,
matching pattern, no nulls in a column. True today only because of how upstream
produces the data; nothing enforces it.
**Future edit:** upstream changes, a new path feeds different data, or boundary
validation is relaxed.
**Hardening:** validate at the boundary; handle the empty/null/out-of-range case
explicitly; encode the assumption as a type or a guard.

### 5. Coincidental correctness
Right answer for the wrong reason: a condition that works only because two variables
happen to be equal today; a loop that never gets the empty case; a broad `except`
that currently sees only one exception type.
**Future edit:** the coincidence stops holding — the input space widens, a new
exception appears, the once-equal variables diverge.
**Hardening:** make the real invariant explicit and test it; narrow the exception
handler; cover the boundary case.

### 6. Non-atomic compound operations
A sequence that should be atomic but is not: check-then-act, multi-step state updates
with no rollback, file/IO ops assuming no concurrent access. An interruption between
steps leaves an inconsistent state.
**Future edit:** someone adds concurrency, moves the code somewhere interruption is
possible, or inserts an early return between steps.
**Hardening:** use a transaction / lock / compare-and-swap; make the operation
idempotent; design for safe retry.

### 7. Invisible invariants
Relationships that must hold but are kept only by convention: "this list and that
dict share keys", "this counter equals len(that)", "this field is non-None whenever
that flag is true". No assertion or type enforces it.
**Future edit:** someone updates one side of the invariant and not the other,
especially across functions/files.
**Hardening:** assert the invariant where it must hold; co-locate the two sides;
encode it in a single structure so it cannot drift.

### 8. Load-bearing defaults
A default (parameter, config, class attribute, env var) the code silently depends on
— it would behave wrongly or dangerously with a different, equally-reasonable value,
and nothing documents the constraint.
**Future edit:** someone changes the default, or a caller starts passing an explicit
value nobody anticipated.
**Hardening:** validate the value where it is used; document why the default matters;
fail fast on a value outside the safe range.

### 9. Implicit resource lifecycle
Resources (connections, file handles, locks, temp files, background tasks) whose
cleanup depends on a particular control flow, with no context manager or finally.
**Future edit:** someone adds an early return, raises an exception, or splits the
function, and cleanup is no longer reached.
**Hardening:** use a context manager / `finally` / RAII; tie the resource's lifetime
to a scope; verify cleanup on every exit path.

### 10. Version-coupled assumptions
Reliance on a specific version's behaviour — dict ordering, an undocumented side
effect, the exact text of a third-party error message, a protocol quirk.
**Future edit:** the dependency or runtime is upgraded, or the undocumented behaviour
shifts.
**Hardening:** pin the dependency and document the reliance; depend only on documented
behaviour; add a test that fails if the assumption breaks.

---

This catalogue is conceptually adapted (MIT) from honnibal/claude-skills and
karim-bhalwani/agentic-harness; see `CREDITS.md`. Stack addenda say
"Extends Category N" to attach technology-specific patterns to these ten.

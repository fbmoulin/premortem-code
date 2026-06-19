# Functional eval fixtures (R1-PRC009 / R2-PRC003)

Two minimal Python+Redis "diffs" with a known ground truth:

- `fixture_bug.py` — a check-then-act race on `slots:<event_id>` (GET then SET,
  non-atomic). Ground truth: premortem-code MUST surface a `high` concurrency finding
  (catalog cat 6 + stack-redis-arq "non-atomic multi-key update"). Expected verdict
  REWORK (structural) or at least REFINE-with-high.
- `fixture_clean.py` — the atomic version (INCR then conditional DECR). Ground truth:
  no real fragility. Budget: 0 `high` findings, ≤2 spurious findings total.

These are the falsifiable floor for "behaviour-equivalence": recall on the bug,
precision on the clean.

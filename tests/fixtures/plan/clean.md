# Plan — add loyalty points [EVAL FIXTURE: correct plan]

## T1 — Schema + idempotent backfill
Add `loyalty_points` with `ADD COLUMN IF NOT EXISTS`. Backfill with an absolute
assignment so re-runs converge: `UPDATE accounts SET loyalty_points = total_spent/10`.
Verify: row count updated == row count expected; re-running changes nothing.

## T2 — API endpoint
Expose `GET /accounts/{id}/points`. Acceptance: returns the stored value for a known
account and p95 latency < 100 ms under the existing load test.

## T3 — Ship behind a flag
Deploy T1, verify the backfill, then enable T2 behind a feature flag; roll back the flag
if the endpoint errors. Each task has its own verification step.

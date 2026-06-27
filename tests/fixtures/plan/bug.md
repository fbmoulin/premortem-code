# Plan — add loyalty points [EVAL FIXTURE: contains planted plan flaws]

## T1 — Schema + backfill
Add a `loyalty_points` column and backfill it from `total_spent`:
run `UPDATE accounts SET loyalty_points = loyalty_points + total_spent/10`.

## T2 — API endpoint
Expose `GET /accounts/{id}/points`. Acceptance: the endpoint should be fast.

## T3 — Ship
Deploy T1 and T2 together.

<!--
Ground truth (do not feed to the reviewer):
- T1 backfill is additive with no idempotency/rollback → re-run/retry double-applies (cat 4, high).
- T2 acceptance "should be fast" is non-falsifiable (cat 1).
- T3 ships the migration and the API together with no verification seam (cat 7).
-->

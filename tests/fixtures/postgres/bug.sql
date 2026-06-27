-- Migration: backfill loyalty points. [EVAL FIXTURE: contains a planted bug]
-- Non-idempotent: ADD COLUMN has no IF NOT EXISTS, and the backfill is additive,
-- so a re-run (or a retry after a partial failure) double-applies every balance.
ALTER TABLE accounts ADD COLUMN loyalty_points integer NOT NULL DEFAULT 0;

UPDATE accounts
SET loyalty_points = loyalty_points + (total_spent / 10);

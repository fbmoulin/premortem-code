-- Migration: backfill loyalty points. [EVAL FIXTURE: correct, idempotent]
-- IF NOT EXISTS makes the DDL re-runnable; the backfill is an absolute assignment
-- (SET =, not +=) so re-running converges to the same value.
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS loyalty_points integer NOT NULL DEFAULT 0;

UPDATE accounts
SET loyalty_points = (total_spent / 10);

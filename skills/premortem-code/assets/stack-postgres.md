# Stack addendum: PostgreSQL

## When this loads
`psycopg`/`psycopg2`/`asyncpg`/`sqlalchemy`, an `alembic/` directory, or `.sql`
migration files.

## Extends
- Category 6 (non-atomic) — transactions, isolation, check-then-act on rows.
- Category 7 (invisible invariants) — constraints expressed in code, not the schema.
- Category 10 (version-coupled) — relies on driver/PG behaviour.

## Failure-mode patterns
- **Check-then-insert race.** `SELECT ... ; if not exists: INSERT` without a unique
  constraint or `ON CONFLICT` → duplicate rows under concurrency (cat 6).
- **Missing/!idempotent migration.** A migration without a reversible `downgrade`, or
  one not safe to re-run, breaks rollback and replays (cat 6/8). Data migration mixed
  with schema change in one step → partial failure leaves inconsistent state.
- **Long transaction / lock escalation.** Work held inside a transaction (HTTP call,
  large loop) holds row/table locks → contention, deadlocks under load.
- **Invariant in code, not schema.** "These two columns are never both null" enforced
  only in Python; a new write path violates it (cat 7). No `CHECK`/`UNIQUE`/FK.
- **N+1 / unbounded query.** A loop issuing per-row queries, or a `SELECT *` without
  `LIMIT` on a table that grows (cat 4).
- **Implicit isolation assumption.** Logic correct only under SERIALIZABLE but the
  pool runs READ COMMITTED (default) → lost updates (cat 5/10).

## Verification questions
- For every "exists? then write": is there a `UNIQUE`/`ON CONFLICT`, or just app logic?
- Does each migration have a tested `downgrade` and is it safe to re-run?
- Any transaction that spans network I/O or an unbounded loop?
- Are cross-column/cross-row invariants backed by `CHECK`/FK, or only by code?

## Common false positives
- A check-then-act guarded by a unique constraint + `ON CONFLICT` is safe.
- A migration explicitly marked irreversible by design (documented) is not a finding.
- Short transactions around a couple of related writes are correct, not "too long".

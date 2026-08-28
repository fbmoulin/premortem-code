# Stack addendum: Redis / ARQ

## When this loads
`redis`/`aioredis` or `arq` in dependencies; worker definitions, `WorkerSettings`,
or `redis.Redis(`/`create_pool(` usage.

## Extends
- Category 6 (non-atomic) — multi-key ops, check-then-act on keys.
- Category 4 (data assumptions) — job payloads, retries, at-least-once delivery.
- Category 8 (load-bearing defaults) — TTLs, queue names, retry/timeout settings.

## Failure-mode patterns
- **Non-atomic multi-key update.** `GET` then `SET` (or updating several keys) without
  `MULTI`/`WATCH`/Lua → lost updates under concurrency (cat 6). Use atomic ops or a
  transaction/script.
- **Job assumed exactly-once.** ARQ/most queues are at-least-once; a non-idempotent
  job re-run on retry double-applies effects (cat 6). Side effects must be idempotent.
- **Lock without expiry / not released.** A Redis lock with no TTL, or released only
  on the happy path, deadlocks on crash/early-return (cat 9).
- **Cache as source of truth.** Reading a value from Redis assuming it is always
  present; eviction/TTL expiry returns `None` and the code does not handle it (cat 4).
- **Unbounded queue / no `max_jobs`/result TTL.** Backlog grows without limit, or job
  results never expire → memory blow-up (cat 8).
- **`keys *` / blocking command** in a hot path → stalls Redis for all clients.

## Verification questions
- Any GET-then-SET or multi-key write without WATCH/MULTI/Lua? Cite it.
- Is every job idempotent (safe to run twice)? What happens on retry?
- Does every lock have a TTL and a release on all exit paths?
- Is any read treating the cache as guaranteed-present?

## Common false positives
- A single atomic command (`INCR`, `SETEX`, `SET ... NX EX`) is race-safe.
- A job that is naturally idempotent (upsert by key) needs no extra guard.
- A cache miss path that correctly falls back to the source is fine.

# Stack addendum: Python / FastAPI

## When this loads
`pyproject.toml`/`requirements*.txt` with `fastapi`/`starlette`/`uvicorn`, or
significant `.py` with FastAPI imports (`from fastapi import`).

## Extends
- Category 6 (non-atomic) — async concurrency makes interleaving the default.
- Category 9 (resource lifecycle) — async clients, sessions, background tasks.
- Category 4 (data assumptions) — request/response models and validation boundaries.

## Failure-mode patterns
- **Blocking call in an async path.** A sync DB/HTTP/file call inside `async def`
  blocks the event loop; under load every request stalls. Look for `requests.`,
  `time.sleep`, sync ORM calls in async handlers.
- **Dependency with shared mutable state.** A module-level client/dict used as a
  cache in a `Depends` provider, mutated per request → races across concurrent
  requests (cat 2/6).
- **`BackgroundTasks` assumed durable.** Work pushed to `BackgroundTasks` runs in the
  same process; a crash/restart loses it. Treated as a queue → silent data loss.
- **Pydantic model drift.** Response `model` narrower/wider than what the handler
  returns; `response_model` filtering hides fields a consumer expected (cat 3/4).
- **Startup/shutdown ordering.** Resource created in `@app.on_event("startup")` used
  by a handler before lifespan completes, or not closed on shutdown (cat 1/9).
- **Unbounded request body / no timeout** on outbound calls → resource exhaustion.

## Verification questions
- For each `async def` handler: any sync I/O on the hot path? Cite the line.
- Does any `Depends` provider mutate module/global state per request without a lock?
- Is any `BackgroundTasks` use actually relied on as durable?
- Do outbound clients set timeouts and get closed in lifespan/finally?

## Common false positives
- A sync call inside `run_in_executor`/`anyio.to_thread` is NOT blocking the loop.
- `Depends` that only reads immutable config is fine.
- A genuinely fire-and-forget log/metric in `BackgroundTasks` is acceptable.

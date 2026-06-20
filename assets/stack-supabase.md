# Stack addendum: Supabase

## When this loads
`@supabase/supabase-js`, `@supabase/ssr` (or the older `@supabase/auth-helpers-*`)
in dependencies; `createClient(`/`createServerClient(`/`createBrowserClient(` usage;
`SUPABASE_SERVICE_ROLE_KEY`/`SUPABASE_ANON_KEY`/`NEXT_PUBLIC_SUPABASE_*` env vars;
`supabase/migrations/*.sql`, RLS policies (`create policy`, `auth.uid()`,
`auth.jwt()`), `supabase/functions/` edge functions, or `.channel(`/`subscribe(`
realtime calls.

## Extends
- Category 4 (data assumptions) — RLS-filtered reads silently return fewer/zero rows.
- Category 6 (non-atomic) — multi-statement writes split across PostgREST calls.
- Category 8 (load-bearing defaults) — anon vs service-role key, RLS-on-by-default.
- Category 3 (stringly-typed) — policy names, table/column names, JWT claim keys.
- Category 5 (coincidental correctness) — `getSession()` trusted where `getUser()` is needed.

## Failure-mode patterns
- **`getSession()` trusted as authorization.** Code branches on `data.session.user`
  from `getSession()`, which reads the cookie/JWT without revalidating it against the
  Auth server. A later edit gates a sensitive action on it; a tampered or stale cookie
  passes. `getUser()` (or `getClaims()` with verification) is the authorized path —
  the breakage is a silent auth bypass, not an error (cat 5).
- **Query relies on RLS to filter, then someone disables/edits the policy.** A read
  like `.from('orders').select('*')` returns only the caller's rows *because* a policy
  restricts it. A future migration that drops, renames, or loosens that policy (or a
  `select` switched to the service-role client) widens the result set with no code
  change and no test failure — cross-tenant data leak (cat 4, cat 8).
- **Service-role client reachable from a path that takes user input.** The
  service-role key bypasses RLS entirely. A helper created for a trusted server job is
  later imported into a route that forwards a user-supplied filter/id, turning RLS off
  for attacker-controlled queries (cat 8). Anon and service-role clients must not share
  a module a request handler can reach.
- **Multi-step write assumed atomic across PostgREST calls.** Two `.insert()`/
  `.update()` calls (e.g. create row + bump a counter) run as separate HTTP requests;
  an error or early return between them leaves a half-written state with no rollback
  (cat 6). A single RPC/`postgres` function with a transaction is the atomic unit.
- **`@supabase/ssr` cookie handling half-wired.** The SSR client needs both `get` and
  `set`/`remove` (or `getAll`/`setAll`) cookie methods to refresh the session. A
  refactor that drops the write side, or omits the middleware that persists the
  refreshed token, leaves the access token un-refreshed — users get random 401s once
  the short-lived JWT expires, only under real session age (cat 9, cat 1).
- **RLS policy keyed on a JWT claim that upstream stops setting.** A policy uses
  `auth.jwt() ->> 'org_id'` or a custom claim injected by an auth hook. If the hook,
  app_metadata shape, or claim name changes, the policy silently evaluates to false (or
  null) and rows vanish — the SQL is valid, just empty (cat 3, cat 7).
- **Edge function assumes a warm/shared global.** A Deno edge function caches a client
  or computed value in module scope expecting it to persist; isolates are recycled and
  cold-start fresh, so the cache is empty on the next invocation and any
  per-invocation secret read from the wrong scope is stale (cat 8, cat 2).

## Verification questions
- Is any authorization decision made on `getSession()` output rather than `getUser()`/
  verified `getClaims()`? Cite the line.
- For each user-scoped `.from(...).select(...)`, what RLS policy makes it safe, and is
  it created in a migration in this repo? Cite both.
- Is the service-role key ever used on a code path that a request handler can reach
  with user input? Cite where the client is constructed.
- Are any two write calls that must both succeed issued as separate PostgREST requests
  instead of one RPC/transaction?
- Does the `@supabase/ssr` client define cookie write methods and is the refresh
  middleware wired? Cite the cookie handlers.

## Common false positives
- A `getSession()` call used only to decide what UI to render (not to authorize a
  mutation or data access) is fine.
- A `select` against a table that is intentionally public-readable (policy `using
  (true)`) needs no per-tenant guard.
- A service-role client confined to a migration/seed script or a cron job with no
  user-input surface is the correct tool, not a leak.

Provenance: structure mirrors `stack-redis-arq.md`; patterns adapted from general
knowledge of Supabase / PostgREST / RLS failure modes.

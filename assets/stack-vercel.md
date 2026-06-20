# Stack addendum: Vercel

## When this loads
`vercel.json`, `next.config.{js,mjs,ts}`, or `@vercel/*` packages present;
`export const runtime = 'edge' | 'nodejs'`, `export const maxDuration`,
`export const revalidate` / `unstable_cache` / `revalidatePath`; `app/api/`
route handlers or `api/` serverless functions; `process.env.NEXT_PUBLIC_*` /
build-time env reads; `.vercel/` project linkage.

## Extends
- Category 8 (load-bearing defaults) — function timeout, region, runtime, cache TTL.
- Category 10 (version-coupled) — Node/runtime version, build-vs-runtime env semantics.
- Category 2 (shared mutable state) — module-scope globals across warm/cold invocations.
- Category 4 (data assumptions) — ISR/cache serving stale or build-time-frozen data.
- Category 9 (resource lifecycle) — connections/handles in stateless functions.

## Failure-mode patterns
- **`NEXT_PUBLIC_`-prefixed secret leaks to the client.** Renaming a server-only var
  to `NEXT_PUBLIC_*` (to "fix" an undefined-on-client error), or reading a secret in a
  component that ends up client-side, inlines it into the browser bundle at build time.
  It works and looks fine — the secret is just now public (cat 8). The breakage is
  invisible until someone inspects the bundle.
- **Env var read at build time assumed to be live at runtime.** A value read in module
  top-level scope (or in `next.config`) is baked into the build artifact. Changing it
  in the Vercel dashboard later has no effect until a redeploy, because deployments are
  immutable. A future "just update the env var" change silently does nothing (cat 10,
  cat 8).
- **Module-scope global assumed to persist across requests.** An in-memory cache,
  rate-limit counter, or "init-once" flag in module scope survives only within one warm
  instance. Vercel spins up many isolated instances and recycles them, so the counter
  resets and the cache is cold on cold starts — a rate limiter built this way undercounts
  badly under load (cat 2, cat 8).
- **Long task exceeds the function timeout under real input.** Code that finishes in
  dev runs against the plan's `maxDuration` default in production; a later edit adds an
  upstream call or larger payloads, the function is killed mid-flight, and the client
  sees a 504 with a *partial* side effect already committed (cat 8, cat 6). Edge
  functions have stricter limits than Node serverless.
- **ISR / `revalidate` serves data frozen at build or last revalidation.** A page using
  `export const revalidate = 3600` or `unstable_cache` returns data that is up to an
  hour stale; a feature that needs freshness is added to that route without lowering the
  window or calling `revalidatePath`/`revalidateTag`, so users see old data with no
  error (cat 4). `force-static` / default fetch caching has the same trap.
- **Edge runtime can't run a Node-only dependency.** Switching `runtime = 'edge'` (for
  latency) onto a handler that uses a Node API (`fs`, `crypto` Node build, a native
  addon, a large SDK) fails — sometimes only at request time on a specific path rather
  than at build (cat 10). The reverse (assuming `edge` globals on `nodejs`) drifts too.
- **Bundle/function size limit hit by a new heavy import.** Adding a large dependency
  to a route handler can push the function past Vercel's compressed size limit; the
  deploy fails, or tree-shaking quietly drops something. The cause (one import) is far
  from the symptom (deploy error on an unrelated function) (cat 8).

## Verification questions
- Does any secret-bearing value have a `NEXT_PUBLIC_` prefix or get read in
  client-reachable code? Cite the var and where it's read.
- Is any env var read at module/build scope where a runtime change is expected to take
  effect? Cite the read.
- Is any cross-request state (cache, counter, init flag) held in module scope rather
  than an external store? Cite it.
- For long-running handlers, what is the effective `maxDuration` and runtime, and can
  real input exceed it? Cite the config.
- For cached/ISR routes, what is the `revalidate`/cache setting and does any new
  freshness requirement violate it? Cite the directive.

## Common false positives
- A genuinely public value (publishable key, public site URL) under `NEXT_PUBLIC_` is
  correct, not a leak.
- A module-scope constant that is deterministic and read-only (config object, compiled
  regex) is safe to share across requests.
- An ISR page where staleness up to the window is intended (marketing/blog content)
  needs no freshness guard.

Provenance: structure mirrors `stack-redis-arq.md`; patterns adapted from general
knowledge of Vercel / Next.js serverless deployment failure modes.

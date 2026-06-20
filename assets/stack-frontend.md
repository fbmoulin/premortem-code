# Stack addendum: Frontend (React / Next / Vue / Vite)

## When this loads
`react`/`react-dom`, `next`, `vue`, or `vite` in dependencies; `.jsx`/`.tsx`/`.vue`
files; `useEffect(`/`useState(`/`watchEffect(` usage, `app/`/`pages/` route dirs,
`getServerSideProps`/server components, or `NEXT_PUBLIC_`/`import.meta.env` reads.

## Extends
- Category 1 (implicit ordering) — render → effect → cleanup → re-render order; SSR vs client.
- Category 2 (shared mutable state) — closures capturing props/state, module-level singletons.
- Category 6 (non-atomic) — overlapping async fetches resolving out of order.
- Category 9 (resource lifecycle) — subscriptions, listeners, timers, aborts not cleaned up.
- Category 10 (version-coupled) — SSR/CSR rendering parity, framework hydration behaviour.

## Failure-mode patterns
- **Stale closure from a thin dep array.** An `useEffect`/`useCallback` reads `count`
  or a prop but omits it from the deps (often to silence a re-run). A later edit makes
  the callback's correctness actually depend on the fresh value → it keeps firing with
  the value captured at mount. Hides because the first render looks right (cat 2).
- **setState after unmount.** An async handler (`fetch().then(setData)`, a `setTimeout`)
  resolves after the component unmounts. Adding an early navigation or a conditional
  unmount turns this into a "can't update state on unmounted component" warning, or
  worse, a write into a dead tree. No cleanup/`AbortController` on the effect (cat 9).
- **Out-of-order async responses.** A search/typeahead fires a request per keystroke and
  renders whichever resolves last. A later latency change (slower endpoint, retry) lets
  an *earlier* query's response overwrite a *newer* one. Looks fine on a fast network
  (cat 6). Needs request cancellation or a "latest request wins" guard.
- **Index as `key` over reorderable lists.** `key={index}` works while the list is
  append-only; a future edit that adds sort/filter/delete makes React/Vue reuse the
  wrong DOM node → input state, focus, or animation attaches to the wrong row (cat 1).
- **Hydration mismatch from non-deterministic render.** Server and client render differ
  — `Date.now()`, `Math.random()`, `localStorage`, `window`, locale — and someone adds
  such a value to JSX. SSR HTML and first client render diverge; React silently discards
  server markup or throws hydration error only in production build (cat 10).
- **`NEXT_PUBLIC_`/`VITE_` secret leak.** A server-only secret is renamed or copied to a
  `NEXT_PUBLIC_*` / `import.meta.env.VITE_*` var to "make it reachable in a component."
  It is now inlined into the client bundle and shipped to every browser (cat 8/exposure).
- **Listener/subscription added without symmetric removal.** `addEventListener`,
  `ResizeObserver`, a store `subscribe`, or an interval set in an effect with no return
  cleanup. Each remount stacks another live listener → duplicated handlers, leaks (cat 9).

## Verification questions
- For each effect/memo/callback: does the dep array include every reactive value it
  reads? Cite the hook and the missing dep.
- Does every async effect cancel/abort on unmount or ignore stale results? Cite the line.
- Any list `key` derived from array index where the list can reorder/filter/delete? Cite it.
- Does any rendered value depend on `window`/`Date`/`random`/storage during SSR? Cite it.
- Is any secret reachable through a `NEXT_PUBLIC_`/`VITE_`-prefixed env read? Cite it.
- Does every `addEventListener`/subscribe/`setInterval` in an effect have a matching
  cleanup in the same effect's return? Cite the one without it.

## Common false positives
- An effect with an empty `[]` dep array that genuinely runs once and reads only stable
  refs/setters (setters are stable) is correct, not a stale-closure bug.
- A `key` from a stable unique id (`item.id`) on a reorderable list is fine.
- A `NEXT_PUBLIC_`/`VITE_` var holding a value that is *meant* to be public (analytics
  id, public API base URL, feature flag) is not a leak.

Adapted from general knowledge of React/Next/Vue/Vite failure modes.

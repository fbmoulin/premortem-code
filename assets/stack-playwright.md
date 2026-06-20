# Stack addendum: Playwright (E2E tests)

## When this loads
`@playwright/test` in dependencies; `playwright.config.{ts,js}`; `*.spec.ts`/`*.e2e.ts`
test files; `test(`, `expect(`, `page.`, `test.use(`, or fixture (`test.extend`) usage.

## Extends
- Category 2 (shared mutable state) — data/auth/state bleeding between tests and workers.
- Category 5 (coincidental correctness) — assertions that pass for the wrong reason.
- Category 6 (non-atomic) — parallel workers racing on the same backend record.
- Category 8 (load-bearing defaults) — retries, timeouts, `fullyParallel`, worker count.
- Category 9 (resource lifecycle) — fixtures/contexts not torn down between tests.

## Failure-mode patterns
- **Hard wait substituted for auto-waiting.** A `page.waitForTimeout(2000)` is added to
  "fix" a flake. It passes on a fast CI box and flakes on a slow one (or wastes minutes
  everywhere). It also masks the real missing condition, so a later UI change that breaks
  the element goes undetected until the fixed delay happens to be too short (cat 8).
- **Selector coupled to volatile markup.** A locator keyed on a generated class, nth-child
  position, or copy text (`text=Submit`) instead of a role/`data-testid`. A routine CSS
  refactor or i18n change silently makes it match the wrong node or nothing — and a
  too-loose selector may keep matching something, so the test passes meaninglessly (cat 5).
- **Shared backend record across parallel workers.** Tests create/edit the same fixed
  user, account, or slug. Under `fullyParallel`/multiple workers they collide — one test
  deletes the row another is asserting on. Green when run with `--workers=1`, red in CI
  (cat 6). Each test/worker needs its own unique, isolated data.
- **State leaking between tests via shared context/storage.** `storageState`, a logged-in
  session, a seeded DB row, or a module global set in one test is relied on by the next.
  Reordering, sharding, or running a single test in isolation breaks it because the
  precondition was an accident of execution order (cat 2/1).
- **Trivially-passing assertion.** `expect(page.locator('.row'))` with no matcher,
  `expect(true).toBeTruthy()`, or asserting an element *exists* when the bug is its
  *content/state*. The test is green but verifies nothing; a future regression in the
  real behaviour never turns it red (cat 5).
- **Retries / `trace: on-first-retry` masking a real flake.** `retries: 2` turns a 30%-
  failure race into a "passing" suite. A genuine product race condition is hidden as
  "flaky test" noise instead of being surfaced as a defect (cat 8).
- **Fixture without teardown.** A `test.extend` fixture that seeds data, opens a second
  context, or starts a server but yields without an `await use()` cleanup block. Leaked
  contexts/rows accumulate across the run and pollute later tests (cat 9).

## Verification questions
- Any `waitForTimeout`/fixed `sleep` standing in for an auto-waiting assertion? Cite it.
- Is each locator a role/`getByRole`/`data-testid`, or is it coupled to class/position/
  copy that a refactor would change? Cite the fragile one.
- Does any test mutate a fixed/shared record that another test or worker also touches,
  under `fullyParallel`? Cite the shared identifier.
- Does any test depend on state established by a *different* test (order/storageState/
  seed)? Cite the assumed precondition.
- Does every `expect` have a real matcher tied to the behaviour under test, not mere
  existence/truthiness? Cite the weak assertion.
- Does every fixture/extra context/server have teardown after `await use(...)`? Cite the
  one that does not.

## Common false positives
- `page.waitFor*` tied to a real condition (`waitForResponse`, `waitForURL`,
  `expect(...).toBeVisible()`) is correct auto-waiting, not a hard wait.
- A unique-per-test fixture that seeds and tears down its own data is the right pattern,
  not shared-state coupling — even if many tests use the same fixture *factory*.
- `retries` on a suite whose flakes are genuinely environmental (network, third-party
  sandbox) is a reasonable mitigation, not a masked product bug.

Adapted from general knowledge of Playwright E2E failure modes.

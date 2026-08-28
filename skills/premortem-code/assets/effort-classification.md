# Effort / mode classification

Pick the run mode (`quick` / `standard` / `deep`) to match the change's **difficulty and
blast radius**, not its line count. The principle is the same one behind compute-optimal
test-time scaling: spend more adversarial effort only where the problem is genuinely harder
(structural, concurrent, security- or data-critical), and stay cheap where it is not. When in
doubt, **round up** — under-reviewing a risky change costs more than over-reviewing a safe one.

This is **advisory**: it sets a starting mode; the human can always escalate or downgrade.

## Decision table

Read top to bottom; the first matching row wins.

| Signal in the diff | Mode |
|---|---|
| Touches a **sensitive surface** — DB migration, auth/RLS/permissions, concurrency/locks/atomicity, or infra (Docker/K8s/CDK/Terraform) | **`deep`** (never lower) |
| Spans **≥3 modules** or is **large** (≳400 changed LOC) | **`deep`** |
| Multiple modules or a public-interface/contract change, but bounded | **`standard`** |
| Docs- or tests-only | **`quick`** (or skip — see SKILL.md "When NOT to run") |
| Small and local (≲40 LOC, one file/module) with no sensitive signal | **`quick`** |
| Anything else | **`standard`** (default) |

## Optional helper

`scripts/classify_effort.py` applies this table deterministically to a diff:

```bash
git diff | python scripts/classify_effort.py
# or
python scripts/classify_effort.py --diff changes.patch
```

It prints JSON `{recommended_mode, signals, rationale, stats}`. It is conservative by
construction — a sensitive signal forces `deep`, ambiguity rounds up — and it is advisory:
it recommends a starting point, it does not decide.

Conceptually adapted from risk-tiered review funnels (cheap deterministic gates first, then
depth keyed on blast radius) and from compute-optimal test-time scaling (effort ∝ difficulty).

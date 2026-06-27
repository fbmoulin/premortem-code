---
name: premortem-code
description: 'Conducts an adversarial pre-mortem on a proposed code change: assumes it has
  already failed in production and enumerates the concrete, location-pinned ways it breaks
  (concurrency, data integrity, partial rollout, contract/type drift, migrations), drops
  false positives via a verification protocol, and issues a GO/REFINE/REWORK/ABANDON
  verdict with optional SARIF export for GitHub Code Scanning. Use this whenever the user is
  about to merge, ship, deploy, or release a PR, branch, or diff; asks "what could go wrong",
  "is this safe for production", "review the risks before merging", "premortem", or
  "pre-mortem"; or wants a risk assessment of code before it goes live, even when they do not
  say "premortem" explicitly. Stack-aware for Python/FastAPI, Postgres, Supabase, Redis/ARQ,
  Qdrant, agents/MCP, Docker/Kubernetes, Vercel, frontend, n8n, Playwright, AWS CDK,
  fine-tuning, and Anthropic skills. Skip for typo/lint/formatting-only or pure-revert changes.'
license: MIT
metadata:
  author: Felipe Moulin (fbmoulin)
  version: 2.0.0
---

# premortem-code

Adversarial pre-mortem on a proposed code change. You assume the change has **already
failed in production** and reason backward to the fragilities that let it fail — the
risks that pass tests but bite later. Output is a `PREMORTEM-<ISO8601>.md` with a
`GO/REFINE/REWORK/ABANDON` verdict, optionally exported to SARIF for GitHub Code Scanning.

This is **not a bug hunt** (current bugs) and **not a style review**. It looks for
places where a *plausible future edit* breaks something non-obviously.

## Workflow

1. **Determine scope.** PR, branch, commit, or working tree. Get the diff and read the
   full enclosing symbols of changed regions — callers and callees, not just the hunk.
2. **Detect stack(s)** using the table below; note which addenda apply. Load only the
   relevant `assets/stack-*.md`. If a stack is detected but has **no addendum** here,
   fall back to `assets/fragility-catalog-core.md` only and **say so** in the output
   (`addenda_loaded` reflects what was actually loaded).
3. **Run adversarial analysis.** Spawn 1–3 sub-agents per `assets/subagent-prompt.md`
   (count by mode, below; give each a distinct lens when >1). Each hunts the 10
   categories in `assets/fragility-catalog-core.md` plus loaded addendum patterns.
4. **Verify** every candidate through `assets/verification-protocol.md` (Anchor →
   Evidence → Severity → Confidence → Format). Discarded candidates go to "Dropped
   findings" with the gate that failed.
5. **Write the report** to `.premortems/PREMORTEM-<ISO8601>.md` using
   `assets/premortem-md-template.md` (create `.premortems/` if missing). `Location`
   MUST be `file:line` or `file:start-end`.
6. **Assign the verdict** (operational rules below) and fill `risk_counts`.
7. **Optional SARIF.** Run `scripts/sarif_export.py --input <the file>` to produce the
   companion `.sarif.json` for GitHub Code Scanning.

## Stack detection

Load only the addendum for each detected stack. (These 14 are the shipped addenda; other
stacks fall back to the core catalogue per step 2.)

| Trigger | Addendum to load |
|---|---|
| `pyproject.toml`/`requirements*` with FastAPI, or `.py` with `from fastapi import` | `stack-python-fastapi.md` |
| `psycopg`/`asyncpg`/`sqlalchemy`, `alembic/`, or `.sql` migrations | `stack-postgres.md` |
| `redis`/`aioredis`/`arq` in deps, or worker/`WorkerSettings` usage | `stack-redis-arq.md` |
| `qdrant_client` or `@qdrant/js-client-rest` | `stack-qdrant.md` |
| `anthropic`/`@anthropic-ai/sdk`/`openai`, or MCP server/client/tool files | `stack-agents-mcp.md` |
| `Dockerfile`, `docker-compose.y*ml`, `k8s/`, or K8s YAML kinds | `stack-docker-k8s.md` |
| `@supabase/supabase-js`/`@supabase/ssr`, `supabase/` dir, RLS policies, `SUPABASE_*` env | `stack-supabase.md` |
| `vercel.json`, `next.config.*`, `@vercel/*`, edge/serverless runtime exports | `stack-vercel.md` |
| `react`/`next`/`vue`/`vite`, or significant `.jsx`/`.tsx`/`.vue` | `stack-frontend.md` |
| `@playwright/test`, `playwright.config.*`, or `*.spec.ts`/`*.e2e.ts` | `stack-playwright.md` |
| `n8n`/`n8n-nodes-*`, `.workflow.json`, or `n8n-nodes-base.*` node types | `stack-n8n.md` |
| `aws-cdk-lib`/`@aws-cdk/*`, `cdk.json`, or `*.cdk.ts`/`*.cdk.py` | `stack-aws-cdk.md` |
| `SKILL.md`/skill dir structure with bundled `assets/`/`scripts/`/`references/` | `stack-anthropic-skills.md` |
| `peft`/`trl`/`bitsandbytes`/`tinker`, or LoRA/SFT training scripts | `stack-finetuning.md` |

## Modes

- `quick` — 1 sub-agent, report only `high`. ~5-10 min. For small PRs.
- `standard` (default) — 1–3 sub-agents, `high`+`medium`. ~10-20 min.
- `deep` — 3 sub-agents (distinct lenses), `high`+`medium`+`low`+cross-cutting
  contradictions. ~20-40 min. For critical/infra changes.

## Mode selection

If the user did not name a mode, pick one by the change's difficulty and blast radius (not
its line count), per `assets/effort-classification.md`: sensitive surfaces (migrations,
auth/RLS, concurrency, infra) or wide/multi-module changes → `deep`; small local changes →
`quick`; otherwise `standard`. When in doubt, round up. Optionally run
`scripts/classify_effort.py` (`git diff | python scripts/classify_effort.py`) for a
deterministic, advisory recommendation. The choice is a default; the user can override.

## Verdict (operational — runs must converge)

Severity is `high|medium|low` (no "critical"; a source "critical" maps to `high`).
Confidence is `confirmed|likely|speculative` (assigned by the verification protocol).

- **structural** = the fix needs a change to design / public interface / data model /
  cross-module contract, OR touches >1 module. **local** = any fix confined to a single
  function/file. The partition is **exhaustive**: every `high` is structural or local; a
  `high` that is not structural is treated as local.
- `ABANDON` — a **declared premise** of the change is contradicted by a `confirmed`
  finding. Rare.
- `REWORK` — ≥1 `high` **structural** finding. Do not merge as-is.
- `REFINE` — there are findings but every `high` is **local**, or only `medium`/`low`.
  Mergeable after the pointwise fixes.
- `GO` — no blocking finding; only `low`/tracked-for-followup.

The verdict is a recommendation; the human decides. The judge reasoning must be
independent of any "why this change is correct" framing in the PR (no self-grading).

## Output contract

The frontmatter + findings shape is fixed (see `assets/premortem-md-template.md`):
`generated, skill, mode, target, scope, stack_detected, addenda_loaded, verdict,
risk_counts{high,medium,low}, dropped_findings_count`, then `## Detailed findings`
(each: Category, Severity, Confidence, Location `file:line`, Mitigation verified absent,
Failure narrative, optional Hardening), then `## Dropped findings`.

## Bundled files

- `assets/fragility-catalog-core.md` — the 10 universal categories; **always** the baseline.
- `assets/stack-*.md` — per-stack patterns; load per the detection table.
- `assets/subagent-prompt.md` — the adversarial sub-agent template; read when spawning.
- `assets/verification-protocol.md` — the anti-false-positive gates; read before reporting.
- `assets/premortem-md-template.md` — the exact output format; read when writing.
- `assets/effort-classification.md` — how to pick the run mode; read for "Mode selection".
- `scripts/sarif_export.py` — run to export a PREMORTEM to SARIF (do not read into context).
- `scripts/classify_effort.py` — run to get an advisory mode recommendation for a diff.

## When NOT to run

Typo/lint/formatting-only changes, pure reverts, test-only additions, or trivial
dependency bumps. The pre-mortem's friction is not justified there.

See `CREDITS.md` for conceptual provenance and source licenses.

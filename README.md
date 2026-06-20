# premortem-code

A Claude Code skill that runs an **adversarial pre-mortem** on a proposed code change:
it assumes the change has *already failed in production* and reasons backward to the
fragilities that let it fail — the risks that pass tests but bite later. It emits a
`PREMORTEM-<ISO8601>.md` with a `GO / REFINE / REWORK / ABANDON` verdict, and can export
findings to SARIF 2.1.0 for GitHub Code Scanning.

> Reconstructed from verified public sources + a recovered output contract; see
> `CREDITS.md`. Behaviour-equivalent to the original (private) `premortem-code`, not a
> byte-for-byte copy.

## Install

Canonical (copy into your personal skills dir):

```bash
cp -r premortem-code ~/.claude/skills/premortem-code
# verify
ls ~/.claude/skills/premortem-code           # SKILL.md, assets/, scripts/
python3 -c "import yaml" || pip install pyyaml   # for the SARIF exporter
```

Project scope (committed to a repo): `cp -r premortem-code <repo>/.claude/skills/`.

## Use

In any Claude Code session:

> Roda um premortem-code standard nas mudanças desta PR.

Modes: `quick` (high only), `standard` (high+medium, default), `deep` (everything +
contradictions, for critical/infra changes).

Output lands in `.premortems/PREMORTEM-<ISO8601>.md`. Export to SARIF:

```bash
python ~/.claude/skills/premortem-code/scripts/sarif_export.py \
  --input .premortems/PREMORTEM-<ISO8601>.md
# writes the sibling .sarif.json for GitHub Code Scanning
```

## What it covers

The 10-category universal **fragility catalogue** (`assets/fragility-catalog-core.md`)
plus stack-specific addenda for **Python/FastAPI, Postgres, Supabase, Redis/ARQ, Qdrant,
agents/MCP, Docker/Kubernetes, Vercel, frontend (React/Next/Vue/Vite), n8n, Playwright,
AWS CDK, fine-tuning, and Anthropic skills** (14 stacks). Other stacks fall back to the
core catalogue. A
**verification protocol** (`assets/verification-protocol.md`) drops false positives, and
the verdict rubric is operational (mechanical structural-vs-local + Confidence axes) so
two runs converge.

## Structure

```
premortem-code/
├── SKILL.md                     # router: workflow, stack table, verdict rubric
├── assets/
│   ├── fragility-catalog-core.md
│   ├── verification-protocol.md
│   ├── subagent-prompt.md
│   ├── premortem-md-template.md
│   └── stack-{python-fastapi,postgres,supabase,redis-arq,qdrant,agents-mcp,
│       docker-k8s,vercel,frontend,playwright,n8n,aws-cdk,anthropic-skills,finetuning}.md
├── scripts/sarif_export.py      # PREMORTEM .md -> SARIF 2.1.0
├── tests/test_sarif_export.py
├── CREDITS.md  NOTICE  LICENSE
└── docs/superpowers/{specs,plans}/   # spec + plan + Plan Review Log (audit trail)
```

## Notes

- Requires Python ≥ 3.10 and `pyyaml` (exporter only).
- Ships 14 stacks / 18 assets (4 base + 14 stack), matching the original deployment kit's
  coverage. Stacks not in the table fall back to the core fragility catalogue.
- The skill was built and reviewed with the `dev-workflow` + `plan-review-cycle` skills;
  the full Plan Review Log (2 rounds, 21 findings) lives in
  `docs/superpowers/specs/premortem-code-reconstruction.md`.

## License

MIT (see `LICENSE`). Third-party attributions in `NOTICE` and `CREDITS.md`.

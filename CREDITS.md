# Credits & Provenance

`premortem-code` is an original reconstruction. Its conceptual lineage and the
licenses of every source consulted are recorded here (license gate run 2026-06-19).

## Adapted (permissive licenses — concepts/structure reused with attribution)

- **honnibal/claude-skills** (`pre-mortem.md.txt`) — MIT License.
  The 10-category "fragility catalogue" idea, the future-bug post-mortem framing,
  and the calibration discipline ("plausible edits, not a bug hunt"). Reworded in
  our own prose; the categories are concepts, not copied text.
- **karim-bhalwani/agentic-harness** (`skills/guardian/references/fragility-catalogue.md`)
  — MIT License. The standalone reference-file format with a per-category "Hardening"
  line and "Calibration Rules" header.
- **stephenkiers/claude-helpers** (`commands/expert-pre-mortem.md`) — MIT License.
  The "scan the git diff and assess each category" workflow shape.
- **boshu2/agentops** (`skills/pre-mortem/SKILL.md`) — Apache License 2.0.
  The verdict-ladder pattern, the no-self-grading invariant, and the pre-registered
  decision-rule / kill-criteria idea behind our operational verdict rubric.
  (Apache-2.0 NOTICE obligations: see `NOTICE`.)

## Conceptual reference ONLY (restrictive license — NOT copied or paraphrased)

- **IgnatG/terraform-reviewer** (`utils/sarif_export.py`) — **AGPL-3.0**.
  AGPL is strong copyleft; copying or paraphrasing it would impose AGPL on this
  project. We did **not** reuse its code, structure, variable names, or comments.
  Our `scripts/sarif_export.py` is written independently from the public SARIF 2.1.0
  schema (json.schemastore.org/sarif-2.1.0.json) and GitHub's documented Code
  Scanning ingestion requirements (the `security-severity` and `partialFingerprints`
  properties, the result `level` mapping). Those are factual spec requirements, not
  copyrightable expression.

## Output contract

The PREMORTEM markdown/frontmatter shape mirrors the original `premortem-code`
deployment kit's `premortems-README.md` (the user's own artifact), preserved here as
`.research/ORIGINAL-output-contract.md`.

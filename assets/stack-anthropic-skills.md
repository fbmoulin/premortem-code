# Stack addendum: Anthropic Skills

## When this loads
A `SKILL.md` with YAML frontmatter (`name`/`description`), a skill directory under
`.claude/skills/`, `skills/`, or a plugin's `skills/`; bundled `assets/`/`scripts/`/
`references/` referenced from a `SKILL.md`.

## Extends
- Category 3 (stringly-typed contracts) — the description is free-text routing; trigger
  phrases, skill names, and file paths are unchecked strings.
- Category 8 (load-bearing defaults) — the 1024-char description budget and the
  ~500-line SKILL.md disclosure budget are implicit limits nothing validates.
- Category 1 (implicit ordering) — progressive disclosure assumes SKILL.md is read
  before refs, and refs are reachable one hop from it.
- Category 2 (shared mutable state) — instruction conflicts between SKILL.md, CLAUDE.md,
  and bundled refs that the model must silently reconcile.

## Failure-mode patterns
- **Description edited for prose, routing breaks.** Someone tightens the `description`
  for readability and drops the literal trigger phrases ("premortem", "what could go
  wrong") the router matched on (cat 3). The skill still loads in manual tests but
  silently stops auto-triggering in the field — no error, just absence.
- **Description grows past 1024 chars.** A new "use when" clause pushes the frontmatter
  description over the limit (cat 8). Depending on the loader, it is truncated mid-clause
  (losing the newest triggers) or the skill is skipped entirely; nothing in the repo
  flags the overflow.
- **Over-broad triggers cause stealing.** A description widened to catch more cases
  ("any code review", "any risk") now out-competes sibling skills and fires on unrelated
  prompts (cat 3). The regression is invisible until a *different* skill that should have
  won quietly stops being chosen.
- **Reference file moved two hops deep.** A refactor relocates `verification-protocol.md`
  into `assets/protocols/` and updates the link, but progressive disclosure only reliably
  surfaces refs one level from SKILL.md (cat 1). The model proceeds without ever reading
  the gate file, skipping verification with no warning.
- **SKILL.md crosses the disclosure budget.** Inlining content that belonged in a bundled
  ref pushes SKILL.md past ~500 lines (cat 8). The tail — often the verdict rubric or the
  output contract — gets truncated from context, so the model improvises the format.
- **Heavy ALWAYS/NEVER musts contradict a deeper ref.** A new absolute rule ("NEVER write
  files") is added to SKILL.md while a bundled ref still instructs writing the report
  (cat 2). The model picks one nondeterministically; behavior diverges run-to-run with no
  failing test.
- **Bundled script trusted blindly.** A `scripts/*.py` is invoked from the workflow with
  user/diff content passed as args, and an edit makes it `shell=True` or eval-based (cat 2).
  Untrusted input now reaches a shell; the happy-path output looks identical.

## Verification questions
- Does `description:` still contain the literal trigger phrases the skill routes on, and
  is it ≤1024 chars? Cite the frontmatter line.
- Is the description specific enough not to poach prompts meant for sibling skills? Name
  the overlap.
- Is every bundled ref linked exactly one hop from SKILL.md, and does that link resolve?
  Cite each `assets/*` reference.
- Is SKILL.md ≤~500 lines, with heavy detail pushed into refs? Cite the line count.
- Do any ALWAYS/NEVER directives in SKILL.md contradict an instruction in a bundled ref
  or CLAUDE.md? Cite both sides.
- Does any bundled script receive untrusted args and reach a shell/eval? Cite the call.

## Common false positives
- A long, keyword-dense description is fine *as long as* it stays under 1024 chars and the
  triggers are still present — verbosity for routing is intentional, not fragility.
- A SKILL.md that links several bundled refs is healthy progressive disclosure, not
  over-engineering, provided each is one hop deep.
- A single, internally-consistent NEVER rule (e.g. "never run when only tests changed")
  is a guardrail, not an instruction conflict.

Patterns above are adapted from general knowledge of Claude Code skill-authoring failure modes.

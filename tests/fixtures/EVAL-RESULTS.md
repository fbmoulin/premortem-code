# Functional eval results (2026-06-19, independent subagents)

Two blind subagents ran the installed skill on neutral copies of the fixtures.

| Fixture | Expected | Result | Verdict | Pass |
|---|---|---|---|---|
| bug (check-then-act race) | surface a `high` concurrency finding | cat 6 high confirmed (structural) + 1 medium (TTL reset) | REWORK | ✅ recall |
| clean (atomic INCR/DECR) | 0 high, ≤2 spurious | 0 high; the tempting race was DROPPED as a false positive (INCR/DECR atomic, self-correcting); 1 medium (skipped-DECR rollback) + 1 low (no TTL) | REFINE | ✅ precision |

Conclusion (calibrated to what the evidence shows):
- **Precision is the load-bearing result.** On the clean fixture the skill DROPPED the
  tempting race as a false positive (the stack-redis-arq "common false positive" note
  fired) and emitted 0 high — a naive reviewer often *would* flag it, so this carries
  real signal.
- **Recall is weak signal.** A bare `get`/`set` Redis race is something most models catch
  unaided; the bug→REWORK result shows the skill doesn't *miss* it but does not, on its
  own, prove value-add over no skill.

Limitations (honest scope):
- **No baseline run.** With-skill only; the fixtures were not run *without* the skill, so
  the value-add delta is not established. Baseline pass is the obvious next step
  (skill-creator's with/without methodology).
- **Pipeline seam not run fully end-to-end on real input.** The exporter was tested on a
  hand-authored SAMPLE and the skill via chat-returned findings; one run of
  skill → contract-conforming PREMORTEM.md → sarif_export on real input would close it.

This is the falsifiable *floor* for behaviour-equivalence (R1-PRC009 / R2-PRC003), not a
proof of equivalence.

## Baseline comparison (with vs without skill, 2026-06-19)

Two more subagents reviewed the same fixtures with NO skill (plain senior-engineer PR
review) to measure the skill's value-add (delta).

| Config | bug fixture | clean fixture | Distinguishes bug from correct? |
|---|---|---|---|
| baseline (no skill) | No-go, 2 high | **No-go, 2 high** | **No** — both No-go |
| with skill | REWORK, 1 high | **REFINE, 0 high** | **Yes** |

**The measured value-add is calibration, not detection.** Both configs catch the obvious
`get`/`set` race in the bug fixture. The difference is on the *correct* fixture: the
unaided baseline escalated it to No-go with two `high` findings (it flagged the atomic
INCR/DECR as an over-booking race and the rollback as high), while the skill's
verification protocol dropped the over-booking race as a false positive and returned
REFINE / 0 high. So the baseline could **not** tell the buggy file from the correct one;
the skill could. For a CI gate that blocks on REWORK/ABANDON, that precision is the whole
point — without it, correct PRs get blocked as often as broken ones.

Caveat: n=2 fixtures, single run each; indicative, not statistically robust.

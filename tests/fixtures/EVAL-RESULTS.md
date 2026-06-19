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

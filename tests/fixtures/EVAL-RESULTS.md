# Functional eval results (2026-06-19, independent subagents)

Two blind subagents ran the installed skill on neutral copies of the fixtures.

| Fixture | Expected | Result | Verdict | Pass |
|---|---|---|---|---|
| bug (check-then-act race) | surface a `high` concurrency finding | cat 6 high confirmed (structural) + 1 medium (TTL reset) | REWORK | ✅ recall |
| clean (atomic INCR/DECR) | 0 high, ≤2 spurious | 0 high; the tempting race was DROPPED as a false positive (INCR/DECR atomic, self-correcting); 1 medium (skipped-DECR rollback) + 1 low (no TTL) | REFINE | ✅ precision |

Conclusion: the skill recalls the real race AND resists the obvious false positive on
correct code (the stack-redis-arq "common false positive" note fired). Falsifiable
floor for behaviour-equivalence (R1-PRC009 / R2-PRC003) met.

# Stack addendum: Agents / MCP / LLM

## When this loads
`anthropic`/`@anthropic-ai/sdk`, `openai`, MCP server/client files (`mcp`,
`@modelcontextprotocol`), tool/function definitions, multi-agent orchestration.

## Extends
- Category 4 (data assumptions) — model output shape, tool args, token limits.
- Category 6 (non-atomic) — tool calls with side effects, retries.
- Category 8 (load-bearing defaults) — model id, max_tokens, temperature, timeouts.

## Failure-mode patterns
- **Model output assumed well-formed.** Parsing the model's text/JSON without
  validation; a format drift or refusal yields an unhandled parse error or silently
  wrong data (cat 4). Structured output / schema validation absent.
- **Non-idempotent tool on retry.** A tool with side effects (write, email, payment)
  invoked inside a retry/loop with no idempotency key → double execution (cat 6).
- **Prompt-injection via tool results / untrusted content.** External text fed back
  into the model can carry instructions; tools executed without an allowlist or
  human gate → unintended actions (security; treat as high).
- **Unpinned/aliased model id.** `claude-x-latest`-style alias or a snapshot that 404s
  → behaviour shifts under you or breaks in prod (cat 8/10). Pin and verify.
- **No token/timeout budget.** Unbounded context growth or no request timeout →
  cost blow-up / hangs (cat 8).
- **MCP STDIO trust / unbounded tool surface.** An MCP server exposing more tools than
  needed, or trusting client input without validation (cat 4; security).
- **Correlated "council" of agents.** N agents with the same prompt/model treated as
  independent votes → correlated noise, false confidence (cat 5).

## Verification questions
- Is every model output validated before use (schema / try-parse with fallback)?
- Does any side-effecting tool run inside a retry without an idempotency guard?
- Is untrusted content ever able to reach a tool-execution path without a gate?
- Are model ids pinned and verified? Are token/timeout budgets set?

## Common false positives
- A read-only tool re-run on retry is harmless.
- Output used only as freeform text (not parsed) needs no schema.
- A deliberately-diverse multi-agent panel (different prompts/lenses) is not "correlated".

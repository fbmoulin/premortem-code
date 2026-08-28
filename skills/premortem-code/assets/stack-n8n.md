# Stack addendum: n8n

## When this loads
`.workflow.json` exports or `n8n`/`n8n-nodes-*` in dependencies; files containing
node `type` like `n8n-nodes-base.*`, expressions using `{{ }}`, `$json`, `$node`,
`$items`, or a Code node (`mode: runOnceForEachItem`/`runOnceForAllItems`).

## Extends
- Category 4 (assumptions in data transformations) — the items array, `$json` shape per item.
- Category 3 (stringly-typed contracts) — node names referenced in `$node["..."]`, expression field paths.
- Category 6 (non-atomic compound operations) — multi-node side effects with no rollback, webhook retries.
- Category 8 (load-bearing defaults) — `continueOnFail`, retry counts, batch size, HTTP timeout/pagination defaults.

## Failure-mode patterns
- **Single-item assumption on a multi-item stream.** A Code or Set node written against
  `$json` (the first item) or `items[0]` works while upstream emits one item; later a
  filter is loosened or a list endpoint is paged in and the node now silently processes
  only the first of many (cat 4). Iterate over all `items`, do not index `[0]`.
- **`$node["Some Name"]` breaks on rename.** An expression pulls data by literal node
  name; a future edit renames that node in the canvas and every downstream reference
  resolves to `undefined`, which then coerces to an empty string in the next field
  rather than throwing (cat 3). Cite the referencing expression and the node it names.
- **Webhook re-delivery double-applies.** The caller (or n8n's own retry) re-sends the
  same webhook; a workflow that inserts a row or charges an API has no idempotency key,
  so the retry duplicates the effect (cat 6). Dedup on an event id before the side effect.
- **`continueOnFail` swallows a step that later matters.** A node flagged
  `continueOnFail: true` to "make the run robust" passes an empty/error item downstream;
  a later edit adds a node that reads a field from that item and computes on garbage
  instead of stopping (cat 8). The run shows success while data is wrong.
- **No transaction across nodes / partial completion.** Node A writes to system X, node B
  to system Y; B fails and there is no compensating action, leaving X updated and Y not
  (cat 6). A retry of the whole workflow then re-runs A as well. Design A idempotent or
  add an explicit rollback branch.
- **HTTP node without rate-limit / pagination handling.** A Loop or Split-In-Batches feeds
  an HTTP Request node with no batch interval or retry-on-429; a future increase in input
  volume trips the upstream API's rate limit and items fail intermittently (cat 8). Cite
  the missing `batchInterval`/retry config.
- **Expression type coercion hides a wrong value.** `{{ $json.amount + 1 }}` where `amount`
  arrives as a string concatenates instead of adds; works while upstream sends a number,
  breaks when a new source sends a numeric string (cat 4). Coerce explicitly (`Number(...)`).

## Verification questions
- Does any Code/Set/IF node read `$json` or `items[0]` while upstream can emit many items?
  Cite the node and its mode (`runOnceForEachItem` vs `runOnceForAllItems`).
- Which expressions reference a node by literal name (`$node["..."]`/`$("...")`)? List each;
  a rename silently nulls them.
- For every webhook/trigger that causes a write or external call: is there an idempotency
  key, and what happens on re-delivery or n8n retry?
- Which nodes set `continueOnFail` (or have no error-workflow), and does anything downstream
  consume their output assuming success? Cite the line/node.
- Do HTTP Request nodes in a loop set a batch interval and retry/backoff for 429s?

## Common false positives
- A node legitimately in `runOnceForAllItems` mode that aggregates the whole `items`
  array (e.g. a single summary call) is meant to see all items — not a single-item bug.
- A naturally idempotent webhook target (upsert by external id, PUT to a fixed key) needs
  no extra dedup guard.
- `continueOnFail` on a node whose failures are routed to a dedicated error branch (and
  nothing on the happy path reads its output) is a deliberate, safe pattern.

---

Conceptually adapted from general knowledge of n8n failure modes.

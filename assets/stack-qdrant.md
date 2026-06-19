# Stack addendum: Qdrant (vector DB)

## When this loads
`qdrant_client` (Python) or `@qdrant/js-client-rest`; `QdrantClient(`, collection
creation, `upsert`/`search` calls.

## Extends
- Category 4 (data assumptions) — vector dimension, distance metric, payload shape.
- Category 7 (invisible invariants) — embedding model ↔ collection coupling.
- Category 10 (version-coupled) — embedding model version baked into stored vectors.

## Failure-mode patterns
- **Dimension/metric mismatch.** Collection created with one vector size/distance; a
  later change to the embedding model emits a different dimension → upsert/search
  errors or silently meaningless scores (cat 4/7).
- **Embedding model drift.** Vectors stored with model A; queries embedded with model
  B (upgrade) → similarity is garbage but no error is raised (cat 10). The collection
  must be re-indexed on model change; nothing enforces this.
- **`recreate_collection` data loss.** Using `recreate_collection` (drops + recreates)
  where `create_collection`/idempotent ensure was meant → wipes data on deploy (cat 6/8).
- **Unbounded/Unfiltered search.** No `limit`/`score_threshold`, or no payload filter
  where one is required → wrong results or huge responses (cat 4).
- **Non-atomic upsert + external write.** Writing the vector and its source-of-truth
  row in two steps with no reconciliation → orphaned vectors on partial failure (cat 6/7).
- **Payload schema assumed.** Reading a payload key that newer points don't set (cat 3/4).

## Verification questions
- Is the collection's vector size/distance pinned to a specific embedding model, and
  is there a re-index step when that model changes?
- Any `recreate_collection` on a path that runs at deploy/startup?
- Do searches set `limit` and the required filters?
- Are vector writes reconciled with their source-of-truth records?

## Common false positives
- A `recreate_collection` in a test/fixture setup is fine.
- A search without a filter where the whole collection is the intended scope is fine.
- Dimension is validated at startup against the model → not a finding.

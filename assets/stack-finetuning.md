# Stack addendum: Fine-tuning (LoRA / PEFT / TRL)

## When this loads
`peft`, `trl`, `bitsandbytes`, `transformers`, or `tinker` in dependencies; training
scripts using `LoraConfig`, `SFTTrainer`/`DPOTrainer`, `BitsAndBytesConfig`, or
`get_peft_model`/`PeftModel.from_pretrained`; chat-template / `apply_chat_template` usage.

## Extends
- Category 4 (data assumptions) — train/eval splits, label shape, dataset distribution.
- Category 3 (stringly-typed contracts) — chat templates, special-token strings, model
  IDs as strings.
- Category 8 (load-bearing defaults) — learning rate, precision (bf16/fp16), 4-bit config,
  `lora_alpha`/`r` ratios.
- Category 10 (version-coupled) — unpinned base-model, tokenizer, and dataset revisions.

## Failure-mode patterns
- **Split done after shuffle/dedup edit → leakage.** A refactor moves dedup or
  augmentation *before* the train/eval split, or splits by row index on an already-
  concatenated frame (cat 4). Near-duplicate prompts land in both sets; eval loss drops,
  the model looks great, and the leak is invisible until production generalization fails.
- **Chat template drifts from the base model.** Someone bumps the base model or hand-writes
  the prompt format, and the training template no longer matches the model's native
  `apply_chat_template` (special tokens, role markers, BOS handling) (cat 3). Training
  "works", but inference with the correct template sees an out-of-distribution format and
  degrades silently.
- **Adapter trained against a different base than it loads onto.** The training base
  (`Qwen3.5-9B`) and the inference `PeftModel.from_pretrained(base, adapter)` base diverge
  after a model-ID edit (cat 3, cat 10). Shapes may still line up (same arch/size), so it
  loads without error and produces quietly worse outputs.
- **fp16 swapped in where bf16 was assumed.** A perf/compat edit changes `bf16=True` to
  `fp16=True` (or vice-versa) without adjusting the LR or loss scaler (cat 8). fp16 on a
  bf16-trained recipe overflows/NaNs late in training, or trains to a worse optimum;
  short smoke runs never reach the regime where it breaks.
- **Resume from checkpoint is non-deterministic.** Adding `resume_from_checkpoint` without
  restoring RNG/data-sampler/optimizer state, or with a changed `per_device_batch_size`/
  grad-accum, silently re-feeds or skips data (cat 6, cat 1). The resumed run diverges from
  an uninterrupted one with no error.
- **4-bit config inconsistent between train and load.** `BitsAndBytesConfig`
  (`bnb_4bit_quant_type`, `compute_dtype`, double-quant) differs between training and the
  later merge/inference load (cat 8). The adapter was tuned against a different quantized
  base; accuracy quietly drops, no exception.
- **Eval set contaminated by a new data source.** A new corpus is appended to training data
  that overlaps the held-out benchmark (cat 4). Metrics inflate; the contamination is
  undetectable from the training logs alone.
- **Unpinned model/dataset versions.** Loading by bare name (`load_dataset("x")`,
  `from_pretrained("org/model")`) with no `revision`/commit hash (cat 10). An upstream
  re-upload changes tokenizer vocab or data rows; the same script now trains a different
  model, reproducibly only by luck.
- **Catastrophic forgetting from over-broad LoRA.** Raising `r`/`lora_alpha` or adding
  target modules to chase a metric (cat 8) over-writes general capability; the target task
  improves while unrelated abilities regress, and the SFT eval set never measures it.

## Verification questions
- Is the train/eval split performed before any dedup/augmentation that could span sets,
  and is there a duplicate check across splits? Cite the split line.
- Does the training prompt format match the base model's `apply_chat_template` exactly
  (special tokens, roles, BOS/EOS)? Cite the template construction.
- Are the training base model ID and the inference/merge base model ID the same string?
  Cite both.
- Is precision (`bf16`/`fp16`) consistent with the LR/scaler choice, and unchanged between
  train and load? Cite the `TrainingArguments`/`SFTConfig`.
- Does resume restore RNG, sampler, optimizer state and keep batch/grad-accum constant?
  Cite the resume call.
- Is the `BitsAndBytesConfig` identical at train and load time? Cite both configs.
- Are base model and dataset pinned to a `revision`/commit? Cite each load call.

## Common false positives
- A held-out eval set drawn from a different *source* than training is good practice, not
  leakage — the concern is overlap, not difference.
- `bf16=True` on an Ampere+ GPU with a recipe tuned for it is correct; precision is only
  fragile when it is changed or mismatched, not merely present.
- A small `r` (e.g. 8–16) with matched `lora_alpha` is a deliberate capacity choice, not an
  under-fit risk; do not flag conservative LoRA rank as fragility.

Patterns above are adapted from general knowledge of LoRA/PEFT/TRL fine-tuning failure modes.

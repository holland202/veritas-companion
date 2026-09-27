# C004: does the companion hold up beside many different large models? Registration

Status: **Registered** (2026-09-27), before any run. No pilot: C004 reuses C001's frozen task, arms
and thresholds unchanged. The only new thing is the list of models, frozen in `MODELS.txt` from the
operator's `--list-models` output on 2026-09-27.

## Why

A result that holds for one model can be an accident of that model. C004 asks C001's question of
every text model the operator's NVIDIA key can reach (37 listed), from 2B to 550B parameters, from
many makers. It is one way of trying to break the claim.

## Frozen setup

- Task and arms: C001 (`task.py`, BASELINE / COMPANION / N1 / N2), **seed 1** only, to keep the number
  of API calls bounded (about 40 per model).
- **Qualifying probe:** before its C001 run, each model must answer one plain lookup on a 3-line log
  correctly within 16 tokens. A model that fails the probe, or that the API will not serve
  (retired, not found, repeated errors), is reported with its reason and **not scored**. This keeps
  "model cannot do the format" (reasoning models that spend their 16 tokens thinking, base models
  that ramble) apart from "companion does not help".
- Costs come from the API's usage field.

## Registered predictions (over the models that qualify and complete)

- **S0 (not vacuous)** At least 10 models qualify and complete.
- **S1 (cost)** The companion's token gain is ≥ 10 on every one of them.
- **S2 (quality)** The companion's accuracy is ≥ the baseline's − 0.10 (one unique question) on at
  least 80% of them.
- **S3 (direction)** The median over them of (companion accuracy − baseline accuracy) is ≥ 0.

## Limits

- One seed per model, one synthetic task (C001's, built to repeat itself). C002 showed that the
  token gain on real logs is far smaller; C004 tests stability across models, not the size of the
  gain on real data.
- Hosted models change without notice; the date and each model's reply are recorded.

# R-NIM amendment (C001 replications, see `../C001_context_economy/REPLICATIONS.md`)

The registered R-NIM model, `meta/llama-3.3-70b-instruct`, is retired (HTTP 410 on 2026-09-27; no run
happened). **Amended before any run:** R-NIM uses `nvidia/llama-3.1-nemotron-70b-instruct`, a 70B
instruct model from the same family, with seeds 1-3 and K1-K6 unchanged.

# R-PHI (added, registered before running)

C001 with the operator's local `Phi-3-mini-4k-instruct-q4.gguf` (3.8B) as the large model, on the S25
CPU (`--device none`, `-c 4096`), seeds 1-3, K1-K6 unchanged. The question is whether the companion
still pays off beside a local model more than twice the size of Qwen 1.5B.

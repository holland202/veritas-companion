# C008 — Adaptive Tier Routing

Evidence-aware cascade: **Tier-0 (deterministic) → Tier-1 (small model) → Tier-2 (large model)**.

## Purpose

Test whether selective escalation reduces inference cost per *verified successful* task
without silently accepting incorrect Tier-1 answers.

This is **not** a claim that a small model is generally as good as a large model.

## Status

| piece | state |
|---|---|
| Routing policy & fail-closed contract | **implemented** (`companion/tier1.py`, `Companion(tier1=...)`) |
| Structured Tier-1 schema + evidence check | **implemented** |
| Experiment runner (B0/B1/B2/N1) | **implemented** (`run.py`) |
| ~135M (or any) small local model | **not present** — README of the repo already labels Tier-1 "designed only, NOT TRAINED, not wired" |
| Registered measured result | **blocked** until a real Tier-1 backend exists and PREREG is frozen |

## Quick plumbing check (no model server required)

```bash
python experiments/C008_adaptive_routing/run.py --seed 101 --oracle
```

Under the default `AlwaysEscalateTier1` stub, B1 and B2 must be identical (the stub never
answers). The runner exits non-zero if they diverge.

## Adding a real Tier-1 backend

Implement `Tier1Backend.complete(prompt) -> (text, prompt_tokens, completion_tokens)` and
pass the instance as `Companion(..., tier1=your_backend)`. The model must emit the JSON
schema in `companion/tier1.py` (or anything `parse_tier1_output` accepts). Invalid or
unevidenced `SUPPORTED` answers escalate.

Do not train a new model solely to run C008; wire the smallest practical local model that
is already available in the environment, or document the blocker (as done here).

## Metrics the runner reports

- total tokens, accuracy, false_accept / false_accept_rate
- per-tier call counts
- cost_per_verified_successful_task (token proxy)

See `PREREG.md` for the full contract and interpretation categories.

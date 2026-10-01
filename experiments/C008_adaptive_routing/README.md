# C008 — Adaptive Tier Routing

Evidence-aware cascade: **Tier-0 (deterministic) → Tier-1 (small model) → Tier-2 (large model)**.

## Purpose

Test whether selective escalation reduces inference cost per *correct* task without silently
accepting incorrect Tier-1 answers. This is not a claim that a small model is generally as good
as a large model.

## Status

| piece | state |
|---|---|
| Routing policy & fail-closed contract | **implemented** |
| Structured Tier-1 schema + evidence check | **implemented** |
| `LlamaServerTier1` (local llama.cpp, default :8081) | **implemented** |
| Experiment runner (B0/B1/B2/N1) | **implemented** |
| Qwen ~0.5B GGUF weights | **external pilot candidate only** — not bundled |
| Registered measured result | **not yet** — pilot only; scientific result UNKNOWN |

## Plumbing check (no model server)

```bash
python experiments/C008_adaptive_routing/run.py --seed 101 --oracle
```

Under `AlwaysEscalateTier1`, B1 and B2 must be identical.

## Real Tier-1 pilot (requires llama.cpp on :8081)

```bash
python experiments/C008_adaptive_routing/run.py --seed 101 \
  --tier1-server http://127.0.0.1:8081 \
  --tier1-model qwen2.5-0.5b-instruct-q4_k_m.gguf
```

Pilot seeds must not become registered seeds. No efficiency claim until PREREG is frozen.

## Metrics

- `token_cost_per_correct_task` (Tier-1 + Tier-2 tokens / correct answers)
- accuracy, false_accept_count / rate
- per-tier call counts and token splits
- large-model avoidance, wall time

See `PREREG.md` for the full contract.

# C008: Adaptive Tier Routing — Registration

Status: **Design / pre-registration draft** (not yet frozen for a measured run).

This file records the experiment contract before any held-out evaluation seeds are used.
Pilot seeds must remain disjoint from future registered evaluation seeds.

## Research question

Does adding a ~0.5B Tier-1 layer reduce total computational cost enough to justify its own
inference cost while maintaining the predefined correctness and safety boundary?

(Can an evidence-aware Tier-0 → Tier-1 → Tier-2 cascade reduce `token_cost_per_correct_task`
relative to a large-model-only baseline, without silently accepting incorrect Tier-1 answers?)

## Baselines (required)

| Arm | Behaviour |
|---|---|
| **B0** Large-model-only | Every task → Tier-2. No companion. |
| **B1** Existing companion | Tier-0 → Tier-2 (`Companion` with `tier1=None`). |
| **B2** Adaptive cascade | Tier-0 → Tier-1 → Tier-2 (`Companion(..., tier1=...)`). |

## Tier-1 contract (frozen)

- Structured result only (`Tier1Result` in `companion/tier1.py`).
- `SUPPORTED` requires non-empty evidence that appears in the context lines.
- `UNCERTAIN` / `ESCALATE` / malformed / missing fields / backend error → escalate.
- Tier-1 never overrides a Tier-0 conflict (`UNCERTAIN` from tools).
- No numerical confidence score is treated as proof.
- Cache hits of Tier-1 answers retain evidence and context fingerprint.

## Candidate Tier-1 model (pilot only)

- A local Qwen ~0.5B GGUF is available on the S25 as an **external pilot candidate**.
- Backend: `LlamaServerTier1` (default `http://127.0.0.1:8081`; Tier-2 stays on `:8080`).
- **No model weights are bundled** in this repository. No training is required or performed.
- Pilot runs are **not** registered evaluation results.
- Pilot seeds must not be reused as registered seeds.
- **No efficiency claim is permitted** until a real backend is tested and this PREREG is frozen.
- QNN/HTP/NPU acceleration is not a prerequisite.

When no Tier-1 server is supplied, the runner uses `AlwaysEscalateTier1` (fail-closed stub)
for plumbing checks only.

## Primary metric

`token_cost_per_correct_task` =
  (Tier-1 prompt + completion tokens + Tier-2 prompt + completion tokens)
  / number of tasks whose answer matched task truth

Tier-1 inference cost is never hidden. "Correct" means matched task truth; it is not a synonym
for gate-style "verified".

Also report: accuracy, false_accept_count / rate, total tokens, Tier-0/1/2 call counts,
Tier-1 accepted, large-model avoidance, Tier-1 and Tier-2 token splits, wall-clock time.

## Safety metric (highest priority)

false_accept = Tier-1 answered incorrectly **and** the system accepted it **and** Tier-2 was not invoked.

Desired: uncertain → escalate, never uncertain → guess.

## Dataset discipline

- Pilot (debug) seeds ≠ registered evaluation seeds.
- Record: dataset/source, seed, task count, categories, model versions, prompts, routing
  config, code revision, evaluation config.
- Prefer the existing C003-style task generator so Tier-0 tools can actually fire.

## Negative controls

- **N1** No escalation: Tier-1 forced to answer (exposes whether escalation protects correctness).
- **N2** Random routing (optional if informative).
- **N3** Tier-1-only (optional).

## Interpretation categories (do not collapse)

Positive · Null · Negative · Partial (by task class).

## Scientific boundary

After this implementation the architecture is:

  Tier 0 → real local Tier 1 (when server supplied) → Tier 2 fallback

The scientific result remains **UNKNOWN**. No claim that Tier-1 is useful, accurate, cheaper,
or faster is permitted until a frozen registered run says so.

## Code revision

Record the commit hash that freezes this PREREG and the runner before the first registered run.

# C008: Adaptive Tier Routing — Registration

Status: **Design / pre-registration draft** (not yet frozen for a measured run).

This file records the experiment contract before any held-out evaluation seeds are used.
Pilot seeds, if any, must be disjoint from the registered evaluation seeds.

## Research question

Can an evidence-aware Tier-0 → Tier-1 → Tier-2 cascade reduce total inference cost per
verified successful task relative to a large-model-only baseline, while maintaining a
predefined accuracy threshold and preventing incorrect Tier-1 answers from being silently
accepted?

## Baselines (required)

| Arm | Behaviour |
|---|---|
| **B0** Large-model-only | Every task → Tier-2. No companion. |
| **B1** Existing companion | Tier-0 → Tier-2 (current `Companion` with `tier1=None`). |
| **B2** Adaptive cascade | Tier-0 → Tier-1 → Tier-2 (`Companion(..., tier1=...)`). |

## Tier-1 contract (frozen)

- Structured result only (`Tier1Result` in `companion/tier1.py`).
- `SUPPORTED` requires non-empty evidence that appears in the context lines.
- `UNCERTAIN` / `ESCALATE` / malformed / missing fields / backend error → escalate.
- Tier-1 never overrides a Tier-0 conflict (`UNCERTAIN` from tools).
- No numerical confidence score is treated as proof.

## Primary metric

`cost_per_verified_successful_task` (token count as proxy when monetary cost is unavailable).

Also report: false_accept_count / false_accept_rate, escalation rate, Tier-1 acceptance rate,
large-model avoidance, verified efficiency vs B0/B1.

## Safety metric (highest priority)

false_accept = Tier-1 answered incorrectly **and** the system accepted it **and** Tier-2 was not invoked.

Desired: uncertain → escalate, never uncertain → guess.

## Dataset discipline

- Pilot (debug) seeds ≠ registered evaluation seeds.
- Record: dataset/source, seed, task count, categories, model versions, prompts, routing
  config, code revision, evaluation config.
- Prefer the existing C003-style task generator (or a documented extension) so Tier-0 tools
  can actually fire; do not invent hard tasks solely to make Tier-1 look useful.

## Task categories (minimum mix)

A deterministic/simple lookup · B structured transformation · C multi-field reasoning ·
D ambiguous/conflicting · E outside Tier-0 · F intended for Tier-2.

## Negative controls

- **N1** No escalation: Tier-1 forced to answer (exposes whether escalation protects correctness).
- **N2** Random routing (Tier-1 vs Tier-2 opportunities kept comparable).
- **N3** Tier-1-only (no Tier-2 fallback).

Reuse an existing control if it already answers the same question.

## Known blocker (recorded before any claim)

No ~135M (or other) small local model is wired or trained in this repository
(README status table: "designed only, NOT TRAINED, not wired").

The default Tier-1 backend is `AlwaysEscalateTier1`: a fail-closed stub that always
escalates. Plumbing, logging, verification, and fail-closed behaviour can be tested;
**any claim that Tier-1 reduces Tier-2 calls or tokens requires a real small-model backend
and a frozen registration after that backend is available.**

QNN/HTP/NPU acceleration is not a prerequisite (§14 of the design note).

## Interpretation categories (do not collapse)

Positive · Null · Negative · Partial (by task class).

## Code revision

Record the commit hash that freezes this PREREG and the runner before the first registered run.

# veritas-companion

**A cheap efficiency layer beside a large model: deterministic tools first, a small model second,
the large model only when the cheaper tiers cannot answer with evidence.**

> The companion does not need to know everything the large model knows. It needs to know what the
> large model needs to know, and when to stay out of the way.

The large model still does the hard semantic work. The companion takes the high-volume, low-cost
friction around it: repeated context, repeated questions, simple lookups, conflicting values that
need a flag rather than a guess. The companion never becomes an authority. Each answer comes back
with a status and its evidence, and every delegation is logged, so any saving is measured.

## Status: what exists and what is only designed

| part | state |
|---|---|
| tier 0, deterministic: fingerprint dedup, answer cache, field extraction, conflict detection | **built, tested** (`companion/runtime.py`) |
| delegation log (task, tier, tokens, status, escalation, final answer) | **built** (JSONL) |
| tier 2, large model through a llama.cpp server | **built** (`companion/llm.py`) |
| [C002](experiments/C002_real_log/): the same companion on a real Android log | **4 of 4 held**: every lookup right; more accurate than the model alone on all 3 seeds; 2.67-2.86× fewer tokens. Exact dedup found almost nothing (≤ 8% of lines), so C001's 13.9× does not transfer |
| C001 on the Adreno GPU (R-ADRENO) | **6 of 6 held**; same tokens, some different model answers than on the CPU |
| [C005](experiments/C005_gate_bridge/): every delegation through the sovereign-veritas gate | **3 of 3 held**: 640 records → 640 packages, all CONSISTENT; 480 ALLOWed answers, 0 wrong; every conflict, escalation and cached model answer DEFERred |
| tier 1, small local model (about 135M) for fuzzy-but-small jobs | **designed only, NOT TRAINED, not wired** |
| [C001](experiments/C001_context_economy/): does tier 0 cut the large model's tokens without losing accuracy? | **6 of 6 held** on the S25: 13.9× fewer large-model tokens, 21× less wall time with overhead counted, accuracy within one question of the model alone (equal on seed 1, better on seed 2, one question worse on seed 3) |
| token-veritas context selection as a companion job | designed only |
| veritas-holo state fingerprints (E003) as a companion job | designed only |

<p>
<img src="figures/token_gain.png" width="49%" alt="token saving by condition">
<img src="figures/accuracy.png" width="49%" alt="accuracy with and without the companion">
</p>

Drawn by `scripts/make_figures.py` from the per-seed values in the results files named in the script.

## The measure

    efficiency gain = baseline large-model tokens / (companion cost + remaining large-model tokens)

The measure only counts when accuracy stays within a tolerance registered before the run. A
companion that costs 2,000 tokens to save 1,000 has failed, and so has one that saves tokens by
giving worse answers. In C001, tier 0 spends no model tokens; its time is logged as well.

## Rules

1. **Cheapest adequate tier first:** hash, parse, lookup, count, compare; then the small model;
   then the large model.
2. **The companion proposes; it never overrides.** Statuses: `SUPPORTED` (answered, with the
   lines that support it), `UNCERTAIN` (conflicting evidence: escalate, do not guess), `ESCALATE`
   (outside the cheap tiers), `CACHED`.
3. **Every delegation is logged.** The fields are task_id, task_type, delegated_to,
   companion_seconds, large_prompt_tokens, large_completion_tokens, companion_result, status,
   escalated, final_result, and cached_origin (for a CACHED answer, the tier that produced it).
4. **Controls that must fail:** C001 includes a companion that answers conflicts without escalating
   (N1) and one that prunes context at random instead of deduplicating (N2). If those did as well as
   the real companion, the experiment would be measuring nothing.
5. **Pilot before registration** on seeds the registered run never uses, then pre-register, then
   run fresh seeds. This is the method veritas-holo adopted after E004.

## Where it sits

    large model      semantic reasoning, planning, hard decisions
        ▲ │
        │ ▼
    companion        dedup · cache · extraction · conflict flags · (small model) · escalation
        │
    token-veritas    what deserves expensive tokens      (research repo)
    veritas-holo     structured state and history        (research repo)
    sovereign-veritas  gate and evidence packages        (governance repo)

## Run it

    python -m pytest -q
    python experiments/C001_context_economy/run.py --seed 101 --oracle     # plumbing check, NOT A RESULT
    python experiments/C001_context_economy/run.py --seed 101              # needs llama-server on :8080

Standard library plus NumPy; runs on a phone in Termux.

*Vincit Omnia Veritas.*

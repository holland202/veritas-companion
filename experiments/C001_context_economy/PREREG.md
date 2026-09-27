# C001: does the tier-0 companion cut large-model cost without losing accuracy? Registration

Status: **Registered** (2026-09-27), after the pilot on seeds 101-103
(`results/exploratory/C001_pilot.md`) and before any run on seeds 1-3. The thresholds come from the
pilot and are frozen here. They are not changed after seed 1.

## Frozen setup

- **Task:** `task.py` as committed: 12 assets and 3 fields; each base fact repeated 4 times; 30
  unique heartbeat lines; 4 conflicted assets, each with an UPDATE line (repeated twice) placed after
  the originals. 10 unique questions: 5 plain lookups, 3 conflict lookups and 2 aggregates. Each is
  asked 3 times in shuffled order, 30 asks in all.
- **Large model:** llama-server on the S25, `qwen2.5-1.5b-instruct-q4_k_m.gguf`
  (sha256 6a1a2eb6…9407e, as recorded in sovereign-veritas), CPU only (`--device none`), `-c 4096`,
  temperature 0, seed 0, n_predict 16, stop at a newline, prompt caching on. The runner prints the
  model path, and a run on any other model does not count.
- **Cost:** large-model tokens = prompt tokens counted by the server's `/tokenize` over the whole
  prompt, cached or not, plus generated tokens. Wall time covers the whole arm, companion overhead
  included.
- **Correct answer:** the expected value appears in the answer as a whole word (case-insensitive).
- **Arms:** BASELINE (full raw log on every ask), COMPANION, N1-NO-ESCALATION and N2-RANDOM-DROP, as
  implemented at the commit that adds this file.
- **Seeds 1, 2, 3.**

## Registered predictions

- **K1 (cost)** On every seed, COMPANION's token gain over BASELINE is ≥ 10.
- **K2 (quality)** On every seed, COMPANION's accuracy is ≥ BASELINE's accuracy − 0.10 (one unique
  question).
- **K3 (time, overhead included)** Summed over seeds 1-3, COMPANION's wall time is ≤ 0.6 × BASELINE's.
- **K4 (null N1)** N1's conflict accuracy is 0.0000 on every seed. Guessing on conflicting evidence
  must be caught as wrong.
- **K5 (null N2)** Pooled over seeds 1-3, N2's conflict accuracy is below COMPANION's. Random pruning
  loses evidence that deduplication keeps.
- **K6 (deterministic tier)** COMPANION's plain-lookup accuracy is 1.0000 on every seed.

The aggregate questions carry no prediction. The 1.5B model failed them in the pilot with or without
the companion; they are reported.

## Limits (before running)

- A synthetic log built to contain redundancy. How much real logs repeat is an open question (C002).
- One small model. With a stronger model, the baseline's accuracy may rise and the gap may change.
- Tier 1 (small model) is not built. This tests tier 0 only.

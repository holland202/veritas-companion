# C001 pilot (exploratory; seeds 101-103 are never used for registered runs)

## Seed 101, S25, qwen2.5-1.5b-instruct-q4_k_m.gguf, CPU only (`--device none`), 2026-09-27

```
VERITAS-COMPANION C001 | seed 101 | aarch64 | Python 3.14.6
model: /data/data/com.termux/files/home/models/qwen2.5-1.5b-instruct-q4_k_m.gguf
log: 182 lines, 70 after dedup; 30 questions (10 unique)
arm                 large tok    gain     acc  lookup  conflict   aggr  cache  determ  large  wall s
BASELINE                44082    1.00  0.8000  1.0000    1.0000 0.0000      0       0     30    90.3
COMPANION                3182   13.85  0.8000  1.0000    1.0000 0.0000     20       5      5    10.2
N1-NO-ESCALATION         1274   34.60  0.5000  1.0000    0.0000 0.0000     20       8      2     0.6
N2-RANDOM-DROP           2346   18.79  0.8000  1.0000    0.3333 1.0000     20       6      4    23.7
```

What the pilot shows:

- The companion used 13.85× fewer large-model tokens than the baseline, and 90.3 s of wall time
  against 10.2 s (its own overhead included), at the same accuracy (0.8000).
- The 1.5B model got both aggregate questions wrong with and without the companion (0.0000). Those
  misses belong to the model, not the companion.
- N1 (guess on conflict) got every conflict question wrong (0.0000), as it must.
- N2 (random pruning) lost two of the three conflict questions (0.3333). It also got both aggregate
  questions right (1.0000) where the full and deduplicated contexts did not. With 2 unique aggregate
  questions, that is one draw, not a pattern. It is noted here so that no threshold is set from it.
- Accuracy moves in steps of 0.1, because each unique question is asked 3 times and the cache answers
  the repeats.

## Seeds 102 and 103, same setup, 2026-09-27

```
VERITAS-COMPANION C001 | seed 102 | aarch64 | Python 3.14.6
arm                 large tok    gain     acc  lookup  conflict   aggr  cache  determ  large  wall s
BASELINE                44124    1.00  0.7333  0.8000    1.0000 0.1667      0       0     30    34.4
COMPANION                3183   13.86  0.8000  1.0000    1.0000 0.0000     20       5      5     9.0
N1-NO-ESCALATION         1272   34.69  0.5000  1.0000    0.0000 0.0000     20       8      2     0.5
N2-RANDOM-DROP           1813   24.34  0.6000  1.0000    0.3333 0.0000     20       7      3     9.3

VERITAS-COMPANION C001 | seed 103 | aarch64 | Python 3.14.6
arm                 large tok    gain     acc  lookup  conflict   aggr  cache  determ  large  wall s
BASELINE                44298    1.00  0.7000  0.8000    1.0000 0.0000      0       0     30   205.9
COMPANION                3168   13.98  0.8000  1.0000    1.0000 0.0000     20       5      5    93.0
N1-NO-ESCALATION         1266   34.99  0.5000  1.0000    0.0000 0.0000     20       8      2    11.7
N2-RANDOM-DROP           2350   18.85  0.9000  1.0000    0.6667 1.0000     20       6      4     8.9
```

Across the three pilot seeds:

- **Token gain** was 13.85, 13.86 and 13.98. The context is built the same way each time, so the gain
  barely moves.
- **Accuracy:** the companion scored 0.8000 on every seed. The baseline scored 0.8000, 0.7333 and
  0.7000. On seeds 102 and 103 the baseline missed a plain lookup (0.8000) that the companion's
  deterministic tier answered from the log (1.0000).
- **Wall-time ratio, companion to baseline:** 0.11, 0.26 and 0.45. Seed 103 was slow in every arm
  (baseline 205.9 s against 34.4 s on seed 102), so the phone's load or temperature varied. Timing is
  the noisiest measure here.
- **N1** scored 0.0000 on conflicts on every seed, as its rule forces.
- **N2** scored 0.3333, 0.3333 and 0.6667 on conflicts; the companion scored 1.0000 on every seed.
- **The baseline changed its answer between identical asks.** On seed 102 it got one of six
  aggregate asks right (0.1667), with temperature 0 and prompt caching on. This fits sovereign-veritas'
  finding that `cache_prompt` affects llama.cpp's output. The companion's cache answers repeats
  identically by construction.

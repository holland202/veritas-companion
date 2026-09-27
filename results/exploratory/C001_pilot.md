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

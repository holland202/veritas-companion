# C001: results

Registered in `PREREG.md` (commit 05f1390) after pilot seeds 101-103. Run on the S25 by the operator
on 2026-09-27, seeds 1-3, with the frozen setup. **6 of 6 held.** The runner does not print
verdicts; they are scored below from the pasted numbers, with the arithmetic shown.

## Output (pasted verbatim, S25)

```
VERITAS-COMPANION C001 | seed 1 | aarch64 | Python 3.14.6
model: /data/data/com.termux/files/home/models/qwen2.5-1.5b-instruct-q4_k_m.gguf
log: 182 lines, 70 after dedup; 30 questions (10 unique)
arm                 large tok    gain     acc  lookup  conflict   aggr  cache  determ  large  wall s
BASELINE                44328    1.00  0.8000  1.0000    1.0000 0.0000      0       0     30   294.3
COMPANION                3188   13.90  0.8000  1.0000    1.0000 0.0000     20       5      5     7.5
N1-NO-ESCALATION         1274   34.79  0.5000  1.0000    0.0000 0.0000     20       8      2     0.5
N2-RANDOM-DROP           2310   19.19  0.6000  1.0000    0.3333 0.0000     20       6      4     8.8

VERITAS-COMPANION C001 | seed 2 | aarch64 | Python 3.14.6
arm                 large tok    gain     acc  lookup  conflict   aggr  cache  determ  large  wall s
BASELINE                44628    1.00  0.6000  0.6000    1.0000 0.0000      0       0     30    34.5
COMPANION                3212   13.89  0.8000  1.0000    1.0000 0.0000     20       5      5     9.9
N1-NO-ESCALATION         1286   34.70  0.5000  1.0000    0.0000 0.0000     20       8      2     0.6
N2-RANDOM-DROP           2968   15.04  0.5000  0.6000    0.3333 0.5000     20       5      5    26.3

VERITAS-COMPANION C001 | seed 3 | aarch64 | Python 3.14.6
arm                 large tok    gain     acc  lookup  conflict   aggr  cache  determ  large  wall s
BASELINE                44184    1.00  0.9000  1.0000    1.0000 0.5000      0       0     30   302.4
COMPANION                3178   13.90  0.8000  1.0000    1.0000 0.0000     20       5      5    12.0
N1-NO-ESCALATION         1270   34.79  0.5000  1.0000    0.0000 0.0000     20       8      2     0.4
N2-RANDOM-DROP           2286   19.33  0.6000  1.0000    0.3333 0.0000     20       6      4     9.4
```

## Verdicts

| | registered | measured | |
|---|---|---|---|
| K1 | gain ≥ 10 on every seed | 13.90, 13.89, 13.90 | **HELD** |
| K2 | companion acc ≥ baseline acc − 0.10 on every seed | 0.8 ≥ 0.7; 0.8 ≥ 0.5; 0.8 ≥ 0.8 | **HELD** (seed 3 exactly at the bound) |
| K3 | pooled companion wall ≤ 0.6 × baseline | 29.4 s / 631.2 s = 0.0466 | **HELD** |
| K4 | N1 conflict accuracy 0.0000 on every seed | 0.0000, 0.0000, 0.0000 | **HELD** |
| K5 | pooled N2 conflict accuracy < companion's | 0.3333 < 1.0000 | **HELD** |
| K6 | companion lookup accuracy 1.0000 on every seed | 1.0000, 1.0000, 1.0000 | **HELD** |

## What this shows

- **13.9× fewer large-model tokens, and 21× less wall time in total (overhead included), at equal or
  better accuracy on two of three seeds.** The time ratio pooled over the three seeds is 0.0466.
- **The cheap tier was more reliable than the model on plain lookups.** On seed 2 the model alone
  missed 2 of 5 lookup questions with the full log in front of it (0.6000). The companion answered
  all of them from the log, with the supporting lines attached.
- **Both controls failed as they had to.** Guessing on conflicting values got every conflict wrong.
  Random pruning kept a third of the conflict answers, against all of them for deduplication.

## What went against the companion

- **Seed 3: the baseline scored 0.9000 and the companion 0.8000.** The model alone got one aggregate
  question right (0.5000) on the full log; given the deduplicated log, it got it wrong. K2's tolerance
  covered exactly that one question, so K2 held at its bound. Removing duplicates changes what the
  model sees, and for a model this small that can change an answer either way.
- **Timing depended on the phone's state.** The baseline took 294.3 s and 302.4 s on seeds 1 and 3,
  against 34.5 s on seed 2. The token counts are the stable measure.

## Limits

- A synthetic log built to repeat itself. Real logs are the next test (C002).
- One 1.5B model; the aggregate questions are beyond it either way.
- Tier 0 only. The small-model tier is not built.

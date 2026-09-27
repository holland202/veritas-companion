# C002: results

Registered in `PREREG.md` (commit 1e29b58) after the pilots. Run on the S25 by the operator on
2026-09-27, seeds 1-3, on the frozen logcat capture, with values hidden. **4 of 4 held.** Verdicts are
scored below from the pasted numbers.

## Output (pasted, S25; progress lines omitted)

```
VERITAS-COMPANION C002 | seed 1 | aarch64 | Python 3.14.6
model: /data/data/com.termux/files/home/models/qwen2.5-1.5b-instruct-q4_k_m.gguf
log: logcat_frozen.log, 5450 lines; window at line 1727: 40 lines, 40 after dedup; 8 questions (8 unique)
asks per question 1; exact-line dedup removes 0 of 40 window lines   (N2 is VACUOUS here: nothing to drop, so it equals COMPANION by construction)
arm                 large tok    gain     acc  lookup  conflict  cache  determ  large  wall s
BASELINE                24516    1.00  0.6250  0.6000    0.6667      0       0      8   400.4
COMPANION                9184    2.67  0.8750  1.0000    0.6667      0       5      3     0.9
N1-NO-ESCALATION            0     inf  0.6250  1.0000    0.0000      0       8      0     0.0
N2-RANDOM-DROP           9184    2.67  0.8750  1.0000    0.6667      0       5      3     0.7

VERITAS-COMPANION C002 | seed 2 | aarch64 | Python 3.14.6
log: logcat_frozen.log, 5450 lines; window at line 3687: 50 lines, 48 after dedup; 8 questions (8 unique)
asks per question 1; exact-line dedup removes 2 of 50 window lines
arm                 large tok    gain     acc  lookup  conflict  cache  determ  large  wall s
BASELINE                26183    1.00  0.3750  0.6000    0.0000      0       0      8    65.1
COMPANION                9519    2.75  0.6250  1.0000    0.0000      0       5      3   248.2
N1-NO-ESCALATION            0     inf  0.6250  1.0000    0.0000      0       8      0     0.0
N2-RANDOM-DROP           9395    2.79  0.6250  1.0000    0.0000      0       5      3   160.0

VERITAS-COMPANION C002 | seed 3 | aarch64 | Python 3.14.6
log: logcat_frozen.log, 5450 lines; window at line 2563: 50 lines, 46 after dedup; 8 questions (8 unique)
asks per question 1; exact-line dedup removes 4 of 50 window lines
arm                 large tok    gain     acc  lookup  conflict  cache  determ  large  wall s
BASELINE                26191    1.00  0.6250  0.8000    0.3333      0       0      8   137.4
COMPANION                9171    2.86  0.7500  1.0000    0.3333      0       5      3    76.6
N1-NO-ESCALATION            0     inf  0.7500  1.0000    0.3333      0       8      0     0.0
N2-RANDOM-DROP           9168    2.86  0.7500  1.0000    0.3333      0       5      3    40.0
```

## Verdicts

| | registered | measured | |
|---|---|---|---|
| R1 | companion lookup accuracy 1.0000 on every seed | 1.0000, 1.0000, 1.0000 | **HELD** |
| R2 | companion acc ≥ baseline − 0.125 on every seed | 0.8750 vs 0.6250; 0.6250 vs 0.3750; 0.7500 vs 0.6250 | **HELD** (the companion was higher on all three) |
| R3 | token gain ≥ 2.5 on every seed | 2.67, 2.75, 2.86 | **HELD** |
| R4 | exact dedup removes < 10% of window lines | 0/40, 2/50 (4%), 4/50 (8%) | **HELD** |

## What this shows

- **On a real Android log, the lookup tier transferred intact.** It answered 5 of 8 questions per
  window without the model and got every one right. The 1.5B model alone, reading the same window,
  scored 0.6000, 0.6000 and 0.8000 on the same lookups.
- **So the companion was more accurate than the model alone on every seed** (by 0.25, 0.25 and 0.125),
  with 2.67-2.86× fewer large-model tokens.
- **Exact deduplication has almost nothing to work on in real logs** (at most 8% of lines). The
  saving here is entirely from answering lookups deterministically. C001's 13.9× depended on a log
  built to repeat itself, and it does not transfer.

## Limits

- Wall time was not registered and is not claimed. It swung from 0.9 s to 248.2 s for the same arm
  across seeds, with the phone's load.
- The "conflict" questions are ill-posed on logcat (see `PILOT.md`) and are not scored. N2 was empty on
  seed 1. On seeds 2 and 3 it dropped a few lines and changed nothing.
- The questions come from the same `key = value` reader the lookup tier uses (stated in PREREG).
  One log, one device, one model.

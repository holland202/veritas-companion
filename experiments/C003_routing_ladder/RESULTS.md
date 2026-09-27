# C003: results

## Deterministic part: 3 of 3 held (x86_64, 2026-09-27; seeds 1-20, no language model)

```
C003 deterministic, seeds 1-20: 320 questions
HELD   D1  routing 320/320 = 1.0000; false SUPPORTED on conflicts 0
HELD   D2  naive null wrong on 45/120 L0 questions = 0.3750
HELD   D3  evidence kept: dedup 320/320, random 314/320
VERDICT  3 of 3 held
```

- **Every question got the right status (320/320), and no planted conflict was answered.** Two sources
  that disagree came back UNCERTAIN every time, and so did two task-start lines that disagree.
- **The traps are real:** the naive first-match extractor was wrong on 45 of 120 lookups (0.3750),
  fooled by decoy fields and by conflicting copies.
- **Deduplication kept every piece of evidence it needed (320/320); random deletion of the same number
  of lines lost some (314/320).** The gap is small because most facts appear three times. It is
  measured on evidence, as registered, not on a model's answers.
- **Circularity, as stated in PREREG:** the log generator and the tools are by the same author. This
  shows the pieces fit together and the traps bite. It does not show routing on someone else's log.

## With a model (M1): pending, seeds 1-3 on the S25

## Deterministic part on the S25 (aarch64, Python 3.14.6, 2026-09-27), seed 1

Run by the operator on the phone (the `--nim` arm stopped at the NVIDIA call: `meta/llama-3.3-70b-instruct`
returned HTTP 410, the model is retired):

```
routing correct 16/16; answers correct when SUPPORTED 16/16; false SUPPORTED on planted conflicts 0
null (naive first-match) wrong on L0 lookups: 2/6
evidence each question needs still present: dedup 16/16, random drop of the same number of lines 16/16
```

Seed 1's routing, answers, trap handling and evidence counts match the container's on another CPU
architecture and Python version.

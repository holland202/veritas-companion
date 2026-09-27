# C006b results: deterministic part (x86_64). Model arms NOT RUN yet

## What broke, first

**P1 cannot be tested here, by construction.** The sovereign-veritas bridge ALLOWs only tier-0 tool
answers; large-model answers are DEFERred by policy (`tools/companion_action.py`, docstring lines 9-10).
On HPC the tier-0 tools answer nothing (P2 below), so A1 can never reach the 5 ALLOWs the vacuity guard
asks for, *with or without a model*. This was not noticed at registration. The registration is not
edited; P1 is reported VACUOUS, and the lesson goes to the next registration: check that the safety
prediction's guard is reachable, not only that the data is.

## Output, verbatim (`output_x86_64.txt`)

```
VERITAS-COMPANION C006b | Loghub HPC 2k | x86_64 | Python 3.11.15
2000 log lines, dedup keeps 1999; 185 nodes with >= 3 lines; 60 questions (seed 6); model: no-model (NOT A RESULT: model answers NOT RUN)
  A0 model alone         statuses {'MODEL': 60}  ALLOW 0 (wrong 0)  correct: last 0/20  first 0/20  count 0/20
  A1 companion           statuses {'ESCALATE': 60}  ALLOW 0 (wrong 0)  correct: last 0/20  first 0/20  count 0/20
  A2 no conflict check   statuses {'ESCALATE': 60}  ALLOW 0 (wrong 0)  correct: last 0/20  first 0/20  count 0/20
  A3 tools off           statuses {'ESCALATE': 60}  ALLOW 0 (wrong 0)  correct: last 0/20  first 0/20  count 0/20
  A4 random drop         statuses {'ESCALATE': 60}  ALLOW 0 (wrong 0)  correct: last 0/20  first 0/20  count 0/20
  A5 shuffled            statuses {'ESCALATE': 60}  ALLOW 0 (wrong 0)  correct: last 0/20  first 0/20  count 0/20
VACUOUS   P1  A1 ALLOWed 0, wrong 0 (vacuity guard: fewer than 5 ALLOWed)
HELD      P2  tier-0 SUPPORTED 0/60 (registered: < 30%)
NOT RUN   P3  needs a model
NOT RUN   P4  needs a model
```

The zeros in the correct column are not a result: no model answered (`no-model` returns an empty
string). They do show the scorer gives nothing to an empty answer.

## Scorer self-test (anti-vacuity), verbatim

```
self-test: oracle reader A1 order 1.000 count 1.000; empty answers scored correct 0/60; A5 order 0.250; P3 on oracle HELD
self-test PASS
```

An oracle that reads whatever log it is given scores 1.000 on the true log; on the shuffled log its
order accuracy drops to 0.250 while its count stays exact, so P3 *can* hold and *can* fail. Empty
answers score 0/60.

## Verdicts so far

| | verdict | |
|---|---|---|
| P1 | VACUOUS | 0 ALLOWs; unreachable under the current gate policy (above) |
| P2 | HELD | tier-0 SUPPORTED 0/60 (< 30 % registered) |
| P3 | NOT RUN | needs a model |
| P4 | NOT RUN | needs a model |

## Cost note for the model run

The log is 151,178 bytes, roughly 40k tokens per call; 6 arms × 60 questions = 360 calls. A1, A2 and A3
send identical prompts here (no tool ever answers), so they will agree unless the model is
nondeterministic, which is itself worth seeing.

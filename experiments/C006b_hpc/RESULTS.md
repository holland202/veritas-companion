# C006b results: model run on the S25 (Gemma 4 31B via NVIDIA NIM), 2026-09-27

## What broke, first

1. **The run printed P3 FAILED; by the registered rule it held.** The registration says Q-count may
   change by "no more than 0.05". A1 got 8/20 and A5 7/20, a change of exactly 1/20 = 0.05. In floating
   point `8/20 - 7/20` is `0.050000000000000044`, which `run.py` compared as greater than 0.05. The
   verbatim output keeps `FAILED`. `run.py` now uses exact fractions; re-evaluated on the printed counts:
   `('HELD', 'order accuracy fell +0.450 (need >= 0.25), count changed 0.050 (need <= 0.05)')`.
   The self-test and the x86_64 deterministic output are unchanged by the fix.
2. **The count clause of P3 and all of P4 sit inside this run's own noise.** A1, A2 and A3 send the
   model identical prompts (no tool ever answers, so the three arms differ only in code paths that were
   never reached) at temperature 0. They still scored last 14/15/13, first 12/12/11, count 8/7/8. The
   hosted model is not deterministic; the same-prompt spread is up to 2/20 = 0.10 per question type.
   So "count changed 0.050" (the P3 clause) and "A1 minus A0 +0.033" (P4) cannot be told apart from
   repeat noise. They are reported as held **by the registered rule**, and that is all they mean.
3. **P1 remains VACUOUS by construction** (0 ALLOWs; the gate DEFERs every model answer; see below).

What does stand: **the shuffle control works on a real model.** Order accuracy on the true log was
26-27/40 for A1-A2 (24/40 for A3); on the shuffled log it was 8/40 (first line 1/20). A fall of 0.450
against a same-prompt spread of 0.075 on the order questions. The instrument can see order.

## S25 output, verbatim (`output_aarch64_s25.txt`, SHA-256 `c3fa8dc39e48366baf0b9103d33938b1f51e37b3d5b939f8202988552ae63420`)

```
VERITAS-COMPANION C006b | Loghub HPC 2k | aarch64 | Python 3.14.6
2000 log lines, dedup keeps 1999; 185 nodes with >= 3 lines; 60 questions (seed 6); model: nvidia-nim:google/gemma-4-31b-it
  A0 model alone         statuses {'MODEL': 60}  ALLOW 0 (wrong 0)  correct: last 13/20  first 12/20  count 7/20
  A1 companion           statuses {'ESCALATE': 60}  ALLOW 0 (wrong 0)  correct: last 14/20  first 12/20  count 8/20
  A2 no conflict check   statuses {'ESCALATE': 60}  ALLOW 0 (wrong 0)  correct: last 15/20  first 12/20  count 7/20
  A3 tools off           statuses {'ESCALATE': 60}  ALLOW 0 (wrong 0)  correct: last 13/20  first 11/20  count 8/20
  A4 random drop         statuses {'ESCALATE': 60}  ALLOW 0 (wrong 0)  correct: last 12/20  first 10/20  count 6/20
  A5 shuffled            statuses {'ESCALATE': 60}  ALLOW 0 (wrong 0)  correct: last 7/20  first 1/20  count 7/20
VACUOUS   P1  A1 ALLOWed 0, wrong 0 (vacuity guard: fewer than 5 ALLOWed)
HELD      P2  tier-0 SUPPORTED 0/60 (registered: < 30%)
FAILED    P3  order accuracy fell +0.450 (need >= 0.25), count changed 0.050 (need <= 0.05)
HELD      P4  A1 minus A0 accuracy +0.033 (need >= -0.017)
```

360 calls, 116.4 min, 25,384,506 prompt tokens (sum of the API's own counts in the progress lines).

## Verdicts

| | printed | by the registered rule | what it means |
|---|---|---|---|
| P1 | VACUOUS | VACUOUS | untestable: the gate never ALLOWs a model answer |
| P2 | HELD | HELD | tier-0 tools answered 0/60; everything escalated, as predicted |
| P3 | FAILED | **HELD** (float bug, above) | order clause strongly held (0.450); count clause held at exactly the bound, within noise |
| P4 | HELD | HELD | +0.033 is inside the 0.10 same-prompt spread; no difference shown |

Other numbers worth keeping: the model counts badly (Q-count 6-8/20 in every arm, including the true
log; 71 lines mention a second node, the registered trap). A4 dropped 1 line (dedup removes only 1 of
2,000), so A4 is not a test of dedup on this log.

## Lessons for the next registration

- Compare against bounds in exact arithmetic.
- Measure same-prompt repeat noise *first* (or register A1 twice) and state every bound as larger than it.
- Check that the safety prediction's vacuity guard is reachable under the gate's policy.

## Unrun, left open

P5 (full HDFS log), the mutation corpus, and a repeat of A1 ×5 to measure the noise floor directly.

---

# Before the model run

### P1 unreachable

**P1 cannot be tested here, by construction.** The sovereign-veritas bridge ALLOWs only tier-0 tool
answers; large-model answers are DEFERred by policy (`tools/companion_action.py`, docstring lines 9-10).
On HPC the tier-0 tools answer nothing (P2 below), so A1 can never reach the 5 ALLOWs the vacuity guard
asks for, *with or without a model*. This was not noticed at registration. The registration is not
edited; P1 is reported VACUOUS, and the lesson goes to the next registration: check that the safety
prediction's guard is reachable, not only that the data is.

## Harness changes before any model answer was recorded (2026-09-27)

The first S25 run (`--nim google/gemma-4-31b-it`) printed nothing for 56 minutes: 56:19 elapsed, 00:00:18
CPU, state S+. That is the process waiting on the network, not hung: NimModel times out each call at 180 s
and gives up after 4 tries. It was stopped before finishing and nothing from it is used. Two harness
changes followed; neither touches questions, truth, scoring or arms:
- one progress line per model call on stderr (seconds, prompt tokens, elapsed, ETA);
- `n_predict` 16 -> 96. At 16 tokens a quoted HPC line would be cut short. This was a harness bug in
  `run.py`, found by reading the code during the stalled run, not from any answer.

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

## Verdicts before the model run (x86_64, superseded above)

| | verdict | |
|---|---|---|
| P1 | VACUOUS | 0 ALLOWs; unreachable under the current gate policy (above) |
| P2 | HELD | tier-0 SUPPORTED 0/60 (< 30 % registered) |
| P3 | NOT RUN | needs a model |
| P4 | NOT RUN | needs a model |

## Cost note for the model run

The log is 151,178 bytes, estimated at roughly 40k tokens per call (wrong: the API counted 70,484-70,541); 6 arms × 60 questions = 360 calls. A1, A2 and A3
send identical prompts here (no tool ever answers), so they will agree unless the model is
nondeterministic, which is itself worth seeing.

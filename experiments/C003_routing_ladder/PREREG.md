# C003: does tier 0 know when to answer, when to flag, and when to hand off? Registration

Status: **Registered** (2026-09-27), after a deterministic pilot on seeds 101-103 (16 of 16 questions
routed correctly on each, 0 conflicts answered, and the naive null wrong on 3, 4 and 3 of 6 lookups),
and before any run on seeds 1-20 (deterministic) or 1-3 (with a model).

## What is new

C001 and C002 asked about lookups only. C003 builds a **ladder of question kinds** into a timestamped
log, in which, as in real logs, lines are rarely byte-identical:

| kind | example | correct tier-0 status |
|---|---|---|
| L0 lookup (some with a decoy line such as `pressure_setpoint` nearby) | What is the pressure of P03? | SUPPORTED |
| L0 conflict (a second source disagrees, with no update marker) | same question | **UNCERTAIN**: the log cannot say which value is right |
| L1 count (restarts; some logged twice verbatim) | How many times did P03 restart? | SUPPORTED, counting distinct timestamps |
| L2 relation | Which asset did TASK 2 act on? | SUPPORTED |
| L2 conflict (two start lines disagree) | Which asset did TASK 6 act on? | **UNCERTAIN** |
| L3 order in time | Did P03 stop before P05 started? | SUPPORTED |
| L4 judgement | Which RUNNING asset is closest to overheating? | **ESCALATE** (no tool; the model's job) |

Two lessons from earlier runs are built in:

- **Evidence, not answers, for the pruning control.** R-PHI's K5 failed because the control compared
  the model's answers. C003 asks directly whether the lines each question needs survive: exact
  deduplication versus random deletion of the same number of lines.
- **A null that must be fooled.** A naive extractor takes the first line that mentions the asset and
  the field word. The decoys and conflicts are there to catch it.

## Registered predictions

Deterministic, seeds 1-20, no language model (runs anywhere):

- **D1** At least 99% of all questions, pooled, get the correct status. **Zero** planted conflicts are
  answered as SUPPORTED.
- **D2 (the traps bite)** The naive null gets at least 30% of the L0 questions wrong, pooled.
- **D3 (evidence)** Deduplication keeps the needed evidence for 100% of questions. Random deletion of
  the same number of lines keeps it for fewer, pooled.

With a model, seeds 1-3, on the S25 (qwen2.5-1.5b, CPU, `--expect-model` enforced):

- **M1** On the questions that have a single right answer, the companion's accuracy is ≥ the model
  alone's − 1/13 (one question) on every seed.

## Limits, stated plainly

- **The deterministic part is circular.** The same author wrote the log generator and the tools. D1 shows
  that the pieces fit together and that the traps are real (D2); it does not show that tier 0 would
  route correctly on someone else's log. That needs a log written by someone else, with questions
  written by someone else.
- One synthetic domain; the L4 question has a computable answer, phrased as judgement.

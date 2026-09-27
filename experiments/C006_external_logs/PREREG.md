# C006: the companion and the gate on logs nobody here designed. Registration

Status: **Registered** (2026-09-27), before any question was generated and before any tool, model or
person read the log lines. What was seen before this file: the three files' SHA-256 and the column
header of the structured CSV (`LineId,Date,Time,Pid,Level,Component,Content,EventId,EventTemplate`).

## Why

C001-C005 used tasks and tools written by the same author (Claude, for Chad Holland), which makes the
deterministic results partly circular. C006 removes the author from the two places that matter:

- **The data** is Loghub's HDFS 2k sample, real Hadoop logs collected by other people
  (https://github.com/logpai/loghub; free for research, cite the repository).
- **The truth** comes from Loghub's own structured parse (`HDFS_2k.log_structured.csv`), made by Loghub's
  parser, not by the companion's tools.

What remains ours, and is stated as a limit: the question *templates* below, and the choice of dataset.

## Frozen data

| file | SHA-256 |
|---|---|
| `HDFS_2k.log` | `7c967000980c086ed55fa6544ba4f05fe66d44622795e890c68caf8bbb635035` |
| `HDFS_2k.log_structured.csv` | `729df59774e3dde934044028546d2a55d5e3d4370b9d12fcebbe4c087b2bf7b4` |
| `HDFS_2k.log_templates.csv` | `a07307511f67c9dc1f41ae730ae60dcce8360f2c72742f0b8a3a9cf1a403d1db` |

`fetch.py` downloads them and exits 1 if any hash differs. The data is not committed.

## Questions (templates fixed now, instances drawn by seed)

HDFS lines are about storage blocks (`blk_…` ids in `Content`). Blocks are drawn with
`numpy.random.default_rng(6)` from the blocks that appear at least 3 times in the structured CSV.
Per block:

- **Q-last** "Which event template was logged last for block B?" Truth: the `EventId` of the block's
  highest `LineId`. Depends on order.
- **Q-count** "How many lines mention block B?" Truth: count of rows whose `Content` contains B.
  Does not depend on order.
- **Q-first-component** "Which component logged the first line for block B?" Truth: `Component` of the
  block's lowest `LineId`. Depends on order.

20 blocks × 3 templates = 60 questions. The generator writes them with their answers to a file that the
arms never read.

## Arms

| arm | what runs | isolates |
|---|---|---|
| A0 model alone | the large model, full log in context | baseline |
| A1 companion | tier-0 tools, else the large model; every answer through the sovereign-veritas gate (C005's bridge) | the system |
| A2 no conflict check | companion with `escalate_on_conflict=False` | what conflict detection adds |
| A3 tools off | every question escalated | what routing adds |
| A4 random drop | companion on the log with lines dropped at random, as many as dedup removes | whether dedup keeps evidence better than chance |
| A5 shuffled | companion and model on the log with line order shuffled (seed 6); truth unchanged | **anti-vacuity:** order questions must get worse |

The deterministic part (A1-A5 without a model, gate decisions, false-ALLOW count) runs anywhere. The
model arms need a model: on the S25, `--nim google/gemma-4-31b-it` or a local llama-server.

## Registered predictions

- **P1 (safety) The gate allows 0 wrong answers in A1.** *Vacuity guard:* if A1 ALLOWs fewer than 5
  answers in total, P1 is reported as **VACUOUS**, not held. A gate that allows nothing trivially allows
  nothing wrong.
- **P2 (coverage, predicted low)** Tier-0 tools answer (SUPPORTED) fewer than 30 % of the 60 questions.
  The tools were written for another log format. This prediction says they will mostly *not* apply,
  and that the right behaviour is to escalate.
- **P3 (the shuffle control can fail)** In A5, accuracy on Q-last and Q-first-component falls by at
  least 0.25 against A1 for every arm that answers them. On Q-count it changes by no more than 0.05. If
  order questions do *not* get worse under shuffle, the scoring is broken, and C006 reports that
  instead of any accuracy result.
- **P4 (model arms, on the phone)** On the questions with a single right answer, A1 accuracy ≥ A0
  accuracy − 1/60.

## Unrun, left open

- **P5** The same protocol on a second Loghub system (OpenSSH or Android) with the same templates,
  unchanged.
- The mutation corpus (timestamp formats, interleaving, truncation), applied to this frozen log, after
  C006 reports.

## Limits

The question templates and the dataset choice are ours. Loghub's parse is independent of the
companion, but it is itself a parser with its own errors; a disagreement between it and the raw log
would be reported, not silently resolved. 20 blocks from one 2,000-line sample of one system.

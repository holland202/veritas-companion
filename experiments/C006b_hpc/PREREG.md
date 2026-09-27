# C006b: the companion and the gate on Loghub HPC 2k. Registration

Status: **Registered** (2026-09-27), before any question was generated and before any tool, model or
person read a log line. Successor to C006, which could not run (see `../C006_external_logs/RESULTS.md`).

What was seen before this file, all of it structural and printed by code:
- `../C006b_feasibility/output_x86_64.txt`: key recurrence and guessability for 5 Loghub systems.
- For HPC only: the column header; that 2,000 raw lines align with 2,000 rows; that every row's `Node`
  appears as a token in its raw line and its `Content` inside it; that 71 lines also name another node;
  that the first and last raw line of each of the 185 usable nodes are all distinct (185 of 185), and
  that a random shuffle keeps the same last line 0.232 of the time and the same first line 0.189.

## Frozen data

| file | SHA-256 |
|---|---|
| `HPC_2k.log` | `826e5957b461e65780a8bda5c186c2fcf90fd6c1863721ef9c1ccfa9ada86f88` |
| `HPC_2k.log_structured.csv` | `0787df9cfab7e9495669548315ea8a9a51b02029c0dcfa28944707ad755a8c86` |
| `HPC_2k.log_templates.csv` | `c6b56ad5537b91a95e88a5953f7abfd7e8b36121673a4123eff7bf3e700d6775` |

`fetch.py` downloads them and exits 1 if any hash differs. Source: https://github.com/logpai/loghub
(free for research; cite the repository). The data is not committed.

## Questions

Keys are HPC nodes (the `Node` column). Nodes with at least 3 rows are eligible; 20 are drawn with
`numpy.random.default_rng(6)`. "Line" means a raw line of `HPC_2k.log`, in file order (`LineId`).

- **Q-last** "Quote the last line in this log that was logged by node N." Truth: the raw line with the
  node's highest `LineId`. Depends on order.
- **Q-first** "Quote the first line in this log that was logged by node N." Truth: lowest `LineId`.
  Depends on order.
- **Q-count** "How many lines in this log were logged by node N?" Truth: rows with `Node` = N.
  Does not depend on order. (Lines that merely *mention* N are not counted; 71 lines name another node,
  so this question has a real trap.)

C006 asked for Loghub `EventId`s, which do not appear in the raw log, so no arm could ever have named
one. C006b asks only for things visible in the raw text.

**Scoring (fixed now).** Q-count: correct if the truth integer appears in the answer as a whole number.
Q-last / Q-first: correct if the answer contains the truth line's `LogId` (its first field), or it
contains the truth `Content` and no other line of that node has the same `Content`. Whitespace is
collapsed before matching.

## Arms

As C006: A0 model alone on the full log; A1 companion (tier-0 tools, else the large model; every answer
through the sovereign-veritas gate); A2 `escalate_on_conflict=False`; A3 tools off; A4 random drop of as
many lines as dedup removes (seed 7); A5 shuffled line order (seed 6), truth unchanged.

## Registered predictions

- **P1 (safety)** The gate ALLOWs 0 wrong answers in A1. *Vacuity guard:* fewer than 5 ALLOWs in A1 →
  reported **VACUOUS**, not held.
- **P2 (coverage, predicted low)** Tier-0 tools answer (SUPPORTED) fewer than 30 % of the 60 questions.
- **P3 (shuffle control)** With a model, A5 accuracy on Q-last and Q-first together falls by at least
  0.25 against A1; on Q-count it changes by at most 0.05. If order questions do not get worse, the
  scoring is broken and C006b reports that instead of any accuracy.
- **P4 (model arms)** A1 accuracy ≥ A0 accuracy − 1/60.

P3 and P4 need a model and are run on the S25 (`--nim google/gemma-4-31b-it`). Without one they are
reported NOT RUN.

## Unrun, left open

- **P5** The same protocol on the full HDFS log (Zenodo HDFS_v1), where block histories are intact.
- The mutation corpus on this frozen log, after C006b reports.

## Limits

The templates and dataset choice are ours, and were chosen after the feasibility counts above (counts
only). 20 nodes from one 2,000-line sample of one system.

# C002: the C001 companion on a real log (pilot first; not yet registered)

C001 used a log built to repeat itself. C002 points the same companion (same tiers, same prompt,
same arms) at a log nobody wrote for this test: the llama-server log that the C001 runs produced on
the S25. The one addition to tier 0 is a deterministic `key = value` reader, because a real log has
no "P07 pressure 41" lines. Questions come from the log's own `key = value` lines. A key with one
value in the window is a lookup; a key whose value changes is a conflict, and its answer is the last
value in the window.

Stated in advance: part of the gain comes from each question being asked 3 times, which the cache
answers. That is a property of the question stream, not of the log, and the results will report the
cache's share separately from deduplication's.

Pilot seeds are 101-103. The registered seeds will be 1-3, run on a copy of the log frozen before
registration, so that the log cannot change between pilot and test.

## Pilot, seeds 101-103, on the S25's own llama-server log (2026-09-27)

Log `c002_frozen.log`, 1755 lines, CPU-only qwen2.5-1.5b. Each question was asked 3 times (the
original design).

| seed | window | lines after dedup | baseline tok | companion tok | gain | baseline acc | companion acc | lookup base / comp | conflict base / comp |
|---|---|---|---|---|---|---|---|---|---|
| 101 | line 2, 60 lines | 60 | 72417 | 9067 | 7.99 | 0.5000 | 0.6250 | 0.8000 / 1.0000 | 0.0000 / 0.0000 |
| 102 | line 1, 60 lines | 60 | 72102 | 9027 | 7.99 | 0.5000 | 0.6250 | 0.8000 / 1.0000 | 0.0000 / 0.0000 |
| 103 | line 0, 70 lines | 70 | 83760 | 10482 | 7.99 | 0.5000 | 0.6250 | 0.8000 / 1.0000 | 0.0000 / 0.0000 |

### What the pilot shows, and why it cannot be registered as designed

1. **None of the gain came from deduplication.** No window contained a repeated line: 60 lines
   became 60 after dedup. On this log every line carries a task id, a timing or a counter, so no two
   lines are byte-identical. The redundancy is real, but it is at the level of line templates, not
   exact lines, and tier 0 cannot see it.
2. **The 7.99× is set by the question design, not by the log.** Of 24 asks, the large model answered
   3 (one per unique conflict question). The deterministic tier answered 5, and the cache answered 16
   repeats. 24/3 = 8. Any log would give about the same number.
3. **Both controls were empty here.** N2 had nothing to drop, so it equalled COMPANION exactly. N1
   could not be told apart on conflicts, because the model got every conflict wrong with or without
   the companion (0.0000 on all arms). A control that cannot differ tells us nothing.
4. **What did carry over from C001:** the deterministic tier got every lookup right (1.0000). The
   model alone, with the same window, missed 1 of 5 lookups on every seed (0.8000). Tier 0 was more
   accurate than the model and cost it nothing.
5. **Only the first few lines of the log qualify.** Every usable window starts at line 0-2 (the
   server's start-up settings), so the three seeds are three views of one window, not three samples.

**Answer to "does C001's advantage survive a real workload?":** on this log, only partly. Exact
lookups carried over, both in cost and in accuracy. The deduplication advantage did not: this log
has no exact duplicates for it to remove. The headline 8× came from repeated questions, and I had
built those into the test myself.

### Changes before any registration

- Each question is now asked **once** by default (`--asks 1`). The cache's effect will be measured
  separately, on a question stream that really repeats, and not built into the headline number.
- The runner prints how many lines dedup removed, and says when N2 is vacuous.
- A registered run needs a real log with **real repetition**. The candidate is Android `logcat`
  captured through Shizuku, which the operator has running. Those are system logs that nobody wrote
  for this test.
- Template-level deduplication (collapsing lines that differ only in numbers, while keeping the
  numbers the questions need) is the tier-0 tool this log calls for. That is a new mechanism, so it
  gets its own pilot (C003); it is not slipped into C002.

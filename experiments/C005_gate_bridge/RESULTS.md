# C005 results: CA7 held, 3 of 3 (x86_64, Python 3.11.15, 2026-09-27)

Registered as CA7 in sovereign-veritas `docs/COMPANION_ACTION.md` before this runner was written.
`python experiments/C005_gate_bridge/run.py --sv ~/sovereign-veritas` (C003 tasks, seeds 1-20, each
question asked twice). Output: `output_x86_64.txt`.

```
640 delegation records -> 640 packages
  CACHED     origin deterministic ALLOW  241
  CACHED     origin large_model   DEFER  80
  ESCALATE   origin None          DEFER  20
  SUPPORTED  origin None          ALLOW  239
  UNCERTAIN  origin None          DEFER  60
HELD   CA7a  480 ALLOWed answers, 0 wrong against the truth
HELD   CA7b  0 conflict/escalation/model-cache records not DEFERred
HELD   CA7c  640/640 packages verify CONSISTENT
```

- Every answer the gate let through was right: 480 of 480, all from deterministic tools, direct or
  cached.
- Every answer from the large-model path (here the test double, NOT A RESULT) was DEFERred, including
  the 80 replayed from the cache. Without `cached_origin` (added in `fff7f84` for this work), a cached
  record could not say which tier had answered.
- SUPPORTED 239 against cached-deterministic 241: two questions repeat within a single pass of one
  seed, so their second asking was already a cache hit.

**Limit.** The deterministic half is circular in the way C003 already states: the same author wrote the
task generator and the tools. What C005 adds is the plumbing. The gate's decisions follow from the
log alone, and every decision re-verifies.

## With a real model: google/gemma-4-31b-it (NVIDIA-hosted), S25, seeds 1-5 (2026-09-27)

Run by the operator on the phone (aarch64, Python 3.14.6):
`python experiments/C005_gate_bridge/run.py --sv ~/sovereign-veritas --nim google/gemma-4-31b-it --seeds 1-5`

```
160 delegation records -> 160 packages
  CACHED     origin deterministic ALLOW  60
  CACHED     origin large_model   DEFER  20
  ESCALATE   origin None          DEFER  5
  SUPPORTED  origin None          ALLOW  60
  UNCERTAIN  origin None          DEFER  15
deferred large-model answers that were in fact right: 3 of 20 (what deferring costs; the model is NVIDIA-hosted google/gemma-4-31b-it)
HELD   CA7a  120 ALLOWed answers, 0 wrong against the truth
HELD   CA7b  0 conflict/escalation/model-cache records not DEFERred
HELD   CA7c  160/160 packages verify CONSISTENT
VERDICT  3 of 3 held
```

- **CA7 held with a real model on real hardware.** A real model's answers were DEFERred just as the test
  double's were, and every package verified on the phone.
- **The cost of deferring, measured for the first time:** 3 of the 20 deferred model answers were right.
  Read that number with care. Most deferred questions are planted conflicts, where the log itself cannot
  say which value is right, or open questions with no single truth. For those, "right" cannot be
  scored and they count as not right. So 3 of 20 is not the model's accuracy. It is how often deferral
  withheld a scorable right answer on this task.

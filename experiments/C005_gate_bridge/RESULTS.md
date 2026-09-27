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

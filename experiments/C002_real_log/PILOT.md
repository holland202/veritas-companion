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

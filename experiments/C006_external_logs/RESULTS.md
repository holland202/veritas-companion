# C006 results: COULD NOT RUN AS REGISTERED (kept)

Date: 2026-09-27. Machine: x86_64 container. Output: `output_x86_64.txt`, pasted verbatim:

```
COULD NOT RUN AS REGISTERED: 0 blocks have >= 3 lines, the registration needs 20. 2000 rows, 2200 distinct blocks; (lines per block, blocks): [(1, 2194), (2, 6)]
```

## What broke

The registration assumed HDFS blocks recur across lines. In Loghub's 2k sample they almost never do:
2,194 of 2,200 blocks appear on exactly one line, 6 appear on two, none on three or more. (2,200 blocks
in 2,000 rows because some lines name two blocks.) Loghub's 2k files are a sample of lines from a much
larger log, so each block's lifecycle is cut to a single line.

So none of the 60 registered questions can be generated, and P1-P4 are **not evaluated**. No arm ran; no
model was called; no accuracy exists.

## What this taught

- The design was checked against the column header only, not against the one property it depended on
  (blocks repeating). A one-line count before freezing would have caught it. That count is now in
  `run.py`, which refuses to run instead of crashing when the property is missing.
- Seen after registration, and only now: the per-block line counts above. No log content, no question
  text, no truth value.

## Not done, on purpose

The registration is not edited to fit the data. Changing the block threshold to 1 or 2 now would make
"which event was logged last" trivial or near-trivial, which is a result chosen after seeing the data.
A successor (C006b) must be registered separately, with a feasibility count done *before* freezing:
for example the full HDFS log (block lifecycles intact, about 1.5 GB), or a 2k system whose natural key
does recur (OpenSSH session pids). P5 in the registration stays open.

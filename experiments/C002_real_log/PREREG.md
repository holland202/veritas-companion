# C002: the tier-0 companion on a real Android log. Registration

Status: **Registered** (2026-09-27), after the pilots in `PILOT.md` (the llama-server log; logcat
seeds 101-103) and before any run on seeds 1-3.

## Frozen setup

- **Log:** `~/logcat_frozen.log` on the S25 (5450 lines; `logcat -d -t 5000` through Shizuku,
  captured once and not modified). Values are hidden in all output (`--keys-only`).
- **Model and server:** as in C001 (qwen2.5-1.5b-instruct q4_k_m, CPU only, `-c 4096`).
- **Runner:** `experiments/C002_real_log/run.py` at the commit that adds this file. Each question is
  asked once: 5 lookups (a key with one value in the window) and 3 "conflicts" (a key with several
  values).
- **Seeds 1, 2, 3.**

## Registered predictions

- **R1 (lookups)** The companion's lookup accuracy is 1.0000 on every seed.
- **R2 (quality)** On every seed, the companion's overall accuracy is ≥ the baseline's − 0.125 (one
  question).
- **R3 (cost)** The companion's token gain is ≥ 2.5 on every seed. That follows from 5 of 8 questions
  answered without the model; no dedup gain is assumed.
- **R4 (the workload finding)** Exact-line dedup removes fewer than 10% of window lines on every
  seed. On real logs, byte-identical repetition is rare.

The conflict questions, N1 and N2 carry **no** prediction. The pilot showed that the conflict
questions are ill-posed on logcat and that N2 is usually empty. They are reported, not scored.

## Limits

- One log, one device, one model. Five lookups per seed is a small number.
- The questions come from the same `key = value` reader that the lookup tier uses, so R1 tests the
  pipeline end to end, not an independent judgement of what the right answer is.

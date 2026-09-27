# C001 replications on other hardware and another model. Registration

Status: **Registered** (2026-09-27), before either run. Both replications reuse C001's frozen
predictions K1-K6 and thresholds unchanged (see `PREREG.md`), on the same seeds 1-3 and the same
task. Only the large model's hardware or identity changes.

## R-ADRENO: the same model on the S25's Qualcomm Adreno 830 GPU

- `llama-server-adreno` (OpenCL, `--device GPUOpenCL -ngl 99`, from sovereign-veritas'
  `tools/adreno_opencl_setup.sh`), the same `qwen2.5-1.5b-instruct-q4_k_m.gguf`, `-c 4096`, port 8080.
- Question: does the companion's advantage hold when the large model runs on the GPU, whose
  arithmetic differs from the CPU's (sovereign-veritas found output that differs by backend)?
- K1-K6 as registered. K3's wall time compares arms within this run only.

## R-NIM: a 70B model hosted by NVIDIA as the large model

- `--nim meta/llama-3.3-70b-instruct` (build.nvidia.com). Token costs come from the API's usage
  field. The key is read from `~/.nvidia_api_key` and never printed.
- Question: does the companion still pay off beside a far stronger model? This is the setting the
  companion was designed for: expensive remote intelligence, cheap local layer.
- K1-K6 as registered. A stronger model may answer the aggregate questions that the 1.5B model
  could not. That can raise the baseline's accuracy, and K2 will measure that honestly.
- Known difference: the prompt is sent as one chat message, not a raw completion.

## R-ADRENO: results (S25, Adreno 830 via OpenCL, 2026-09-27). 6 of 6 held

```
VERITAS-COMPANION C001 | seed 1 | aarch64 | Python 3.14.6
arm                 large tok    gain     acc  lookup  conflict   aggr  cache  determ  large  wall s
BASELINE                44328    1.00  0.8000  1.0000    1.0000 0.0000      0       0     30    18.3
COMPANION                3188   13.90  0.8000  1.0000    1.0000 0.0000     20       5      5     5.3
N1-NO-ESCALATION         1274   34.79  0.5000  1.0000    0.0000 0.0000     20       8      2     1.3
N2-RANDOM-DROP           2310   19.19  0.6000  1.0000    0.3333 0.0000     20       6      4     5.0

VERITAS-COMPANION C001 | seed 2 | aarch64 | Python 3.14.6
BASELINE                44628    1.00  0.6000  0.6000    1.0000 0.0000      0       0     30    25.2
COMPANION                3212   13.89  0.9000  1.0000    1.0000 0.5000     20       5      5     4.1
N1-NO-ESCALATION         1282   34.81  0.6000  1.0000    0.0000 0.5000     20       8      2     0.8
N2-RANDOM-DROP           2968   15.04  0.5000  0.6000    0.3333 0.5000     20       5      5     3.9

VERITAS-COMPANION C001 | seed 3 | aarch64 | Python 3.14.6
BASELINE                44184    1.00  0.8000  0.8000    1.0000 0.5000      0       0     30    28.7
COMPANION                3178   13.90  0.8000  1.0000    1.0000 0.0000     20       5      5     5.7
N1-NO-ESCALATION         1270   34.79  0.5000  1.0000    0.0000 0.0000     20       8      2     1.2
N2-RANDOM-DROP           2286   19.33  0.7000  1.0000    0.6667 0.0000     20       6      4     4.9
```

| | measured | |
|---|---|---|
| K1 | 13.90, 13.89, 13.90 | **HELD** |
| K2 | 0.8 vs 0.8; 0.9 vs 0.6; 0.8 vs 0.8 | **HELD** |
| K3 | 15.1 s / 72.2 s = 0.209 | **HELD** |
| K4 | N1 conflict 0.0000 on every seed | **HELD** |
| K5 | N2 pooled conflict 0.4444 < companion 1.0000 | **HELD** |
| K6 | companion lookups 1.0000 on every seed | **HELD** |

The token counts are identical to the CPU run, as they must be: the same tokenizer on the same
prompts. **The answers are not identical.** On seed 2 the companion got an aggregate question right on
the GPU (0.5000) that it missed on the CPU (0.0000). On seed 3 the baseline missed a lookup on the GPU
(0.8000) that it got right on the CPU (1.0000). The same model gives different answers on different
arithmetic hardware, which is what sovereign-veritas found. The companion's deterministic answers
do not depend on the hardware. The GPU baseline was also far faster: 72.2 s in total, against
631.2 s on the CPU.

## R-NIM: could not run (2026-09-27)

All three seeds stopped at the first call with `HTTP Error 410: Gone`: NVIDIA no longer serves
`meta/llama-3.3-70b-instruct`. No result exists. Replacing the model is an amendment to this
registration and will be written here, with the new model named, before any run.

## R-NIM (amended to `nvidia/llama-3.1-nemotron-70b-instruct`): could not run (2026-09-27)

All three seeds returned HTTP 404 on the first call. The amended model is listed for the key but not
served to it. No result. See C004's results for the same problem across 26 listed models.
`google/gemma-4-31b-it` did serve and ran C001 seed 1 inside C004 (gain 13.50, accuracy 0.9000 on both
arms). Any further R-NIM model will be named in an amendment before its run, and chosen only from
models that pass a serving check first.

## R-PHI: did not run (2026-09-27); the runs made were Qwen again

The Phi-3-mini server exited at once (`Exit 1`). The Adreno server, which runs the `llama-server`
binary under a wrapper, was still holding port 8080: `pkill -f llama-server-adreno` matched the
wrapper's name, not the running binary. The three runs therefore went to the still-running Qwen
server. The runner's `model:` line printed `qwen2.5-1.5b-instruct-q4_k_m.gguf`, and that is how the
mix-up was caught. Those runs are not R-PHI. They repeat the Qwen results (seeds 2 and 3 exactly as
in R-ADRENO; seed 1 with 44336 baseline tokens instead of 44328) and add no new claim. R-PHI remains
registered and unrun.

Before a local-model run, the runner should refuse if the server reports a different model file than
the one intended, as sovereign-veritas' `model_action.py` already does (`--model-file`). That guard is
to be added here.

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

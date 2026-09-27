# C004b: the sweep again, done properly (plan; to be registered after the serving probe)

C004 failed its first prediction because the model list came from the key's listing, and 26 listed
models do not serve. C004b fixes the order of work:

1. **Serving probe (no scoring):** `python experiments/C004_model_sweep/run.py --serving-probe ~/c004b_models.txt`.
   Every listed text model gets the one-question probe. Only models that serve and answer it correctly
   within 16 tokens are written out.
2. **Reasoning models are excluded, decided now, before the probe:** a model that spends its answer
   budget thinking is a different experiment (it would need a larger budget and a final-answer parser).
3. **Freeze** the probe output into `MODELS_C004b.txt`, commit it, and register S0-S3 unchanged, with
   S0 lowered to "at least 3 models" only if the probe finds fewer than 10.
4. Run.

## Step 1 run (S25, 2026-09-27) and where C004b stops

Output: `serving_probe_S25_2026-09-27.txt`. The reason column there reads "known; list the ones..."
instead of the HTTP code, because of a display bug introduced the same day (`5bb0312` added a hint to the
error text, and the probe printed its last 60 characters). The probe now prints the HTTP code.

- 37 listed models probed; 3 serve and answer correctly: `google/gemma-4-31b-it`, `mistralai/mistral-nemotron`
  and `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`.
- Step 2, decided before the probe, excludes reasoning models, which leaves **2**.
- Step 3 allowed lowering S0 to "at least 3 models", and no lower. **With 2, C004b is not registered.** A
  sweep across two models cannot say anything about models in general. This is recorded as the outcome of
  the plan, not as a failed prediction. The two serving models remain usable as single large models
  (`--nim`) in other experiments.

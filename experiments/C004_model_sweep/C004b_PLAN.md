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

# C001: pilot first (not yet registered)

Seeds 101-103 are the pilot. The registered run will use seeds 1-3, with thresholds set from what
the pilot shows. With llama-server running on the S25 (any local model; the model's file name is
printed and recorded), paste the output of:

    python experiments/C001_context_economy/run.py --seed 101

Prediction candidates, to be fixed after the pilot:

- the companion cuts large-model tokens by at least some factor G;
- its accuracy is within some tolerance of the baseline's;
- N1 (no escalation on conflict) loses the conflict questions;
- N2 (random pruning) loses accuracy that dedup does not.

The plumbing run with the oracle test double (NOT A RESULT) gave, on seed 101: baseline 17346 tokens,
companion 1192 (gain 14.55) at equal accuracy; N1 0.0 on conflicts; N2 0.3333 on conflicts. A real
model will be less accurate than the oracle on every arm, and the pilot exists to measure how much.

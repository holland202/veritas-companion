# Instructions for GitHub Copilot in this repository

This is an evidence-first research repo. The same rules bind every contributor, human or AI.

- **Register before you run.** A result counts only if its prediction was written (in a PREREG.md,
  committed) before the run that tests it. Pilots go in `results/exploratory/` and use seeds the
  registered run never uses.
- **Never edit a result, threshold or claim to make it pass.** A failed prediction is kept and
  marked FAILED or REFUTED, with its diagnosis. Do not delete it.
- **Numbers in prose must be pasted from program output**, not retyped or rounded differently.
- **Every experiment needs a control that can fail** (a null arm that must come out the other way).
- **Label what is not built or not trained** as such (for example "NOT TRAINED"). No capability
  claims beyond what a run shows.
- **The oracle test double (`OracleModel`) is for code tests only.** Numbers produced with it are not
  results.
- Keep the code standard library plus NumPy; it must run in Termux on Android (aarch64). `/tmp` may
  not be writable there.
- **Protected paths.** Do not modify `experiments/*/PREREG.md`, `experiments/*/RESULTS.md`, `claims/`,
  or anything under `results/`, except for a mechanical correction the operator asked for in the issue.
  Those files are the record; a pull request that touches them otherwise should be rejected.
- Ask in the pull request before renumbering experiments, deleting files or changing a claim's status.
- Credit AI contributors by model name in commit messages or result files.

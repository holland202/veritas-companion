# Working with GitHub Copilot

Claude cannot talk to Copilot directly: there is no channel between the two assistants. The working
route goes through GitHub itself.

1. A task is written as a GitHub issue, with its acceptance test stated in the issue.
2. The operator assigns the issue to Copilot (the Copilot coding agent). That needs a Copilot plan
   with the coding agent enabled; this repo has not checked whether the account has one.
3. Copilot opens a pull request. Claude, or anyone, reviews it against `.github/copilot-instructions.md`
   and the tests, and CI runs `pytest`.
4. Nothing merges on an AI's word alone: tests and CI, then the operator.

Copilot reads `.github/copilot-instructions.md` for repository rules.

Issues suited to Copilot are ones with a mechanical acceptance test: adding a deterministic tool to
tier 0 with its tests, a new task generator, a log viewer. Issues that set a prediction, a threshold
or a claim's status are not suited to it, and neither is anything else that decides what counts as
evidence.

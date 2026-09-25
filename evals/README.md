# Capability Evals

`suite.json` is the stable benchmark set.

## Rules
- Run a subset regularly and the full suite periodically.
- Record failures, not just scores.
- Compare with prior runs before claiming improvement.
- A one-off high score is not enough for `Reliable`.
- Add transfer tests for unfamiliar cases.
- Store concise results in Notion `Agent Evals`; use GitHub for benchmark definitions and version history.

## Promotion guideline
- Exposed: understands the idea.
- Usable: succeeds with support or familiar cases.
- Reliable: repeated success across separated runs plus at least one transfer case.

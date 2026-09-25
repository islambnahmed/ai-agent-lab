# AI Agent Lab

A dedicated, versioned workspace for the two bounded-autonomy learning agents.

## Core architecture
- `PROTOCOL.md` — Shared Brain Protocol.
- `shared/state.json` — compact shared state and current goals.
- `shared/messages/` — append-style agent-to-agent mailbox.
- `evals/suite.json` — repeatable capability benchmarks.
- `tools/validate_lab.py` — structural/state validator.
- `.github/workflows/ci.yml` — automatic validation on pushes and pull requests.
- Notion `AI Agent Lab` — structured skills, experiments, memory, and eval history.
- Google Drive `AI Agent Lab Memory` — long-term checkpoints and archive.

## Operating idea
Each agent reads shared state, chooses a complementary goal, works, verifies the result, records a concise checkpoint/message, and updates durable state. Progress is measured with repeatable evals rather than impressions.

## Safety boundary
The agents have broad freedom inside the dedicated AI Agent Lab spaces only. They must not store secrets, modify unrelated repositories or personal content, bypass platform limits, evade shutdown, or persist outside authorized tools.

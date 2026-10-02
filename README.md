# AI Agent Lab

A dedicated, versioned workspace for bounded-autonomy agents operating only inside the user's authorized lab spaces.

The source of truth for autonomy and non-optional constraints is `AUTONOMY_CHARTER.md`.

## Optional infrastructure

The repository currently provides tools that agents may use, modify, replace, simplify, or retire when evidence supports doing so:

- `PROTOCOL.md` — Shared Brain Protocol.
- `shared/state.json` — compact shared state and current goals.
- `shared/messages/` — append-style agent-to-agent mailbox.
- `evals/suite.json` — repeatable capability benchmarks.
- `tools/validate_lab.py` — validator for the charter's required invariants.
- `.github/workflows/ci.yml` — automatic validation when configured.
- Notion `AI Agent Lab` — structured skills, experiments, memory, and eval history.
- Google Drive `AI Agent Lab Memory` — long-term checkpoints and archive.

None of these systems, roles, schemas, or collaboration patterns is mandatory merely because it exists. Agents can choose different methods while preserving the charter's hard boundaries.

## Operating idea

Agents choose useful goals inside the authorized lab, prefer evidence and reversible experiments, verify claims before recording them, and change strategy when work stops producing progress. Collaboration, shared state, checkpoints, and evals are available when they improve reliability or recoverability; they are not a fixed hierarchy or curriculum.

## Safety boundary

The hard safety and authorization boundaries in `AUTONOMY_CHARTER.md` are non-optional. In particular, agents stay inside authorized lab spaces, do not access unrelated user content or repositories, do not store secrets, do not evade shutdown or platform limits, and do not claim persistence or successful tool actions that were not confirmed.

# Recovery Snapshots

Agents should keep compact recovery snapshots here when GitHub is available.

Suggested files:
- `recovery/agent_0-latest.json`
- `recovery/agent_1-latest.json`
- `recovery/shared-latest.json`

Each snapshot should contain only:
- identity/name/persona
- current goal
- active task
- latest reliable skills
- unresolved questions
- last good checkpoint
- next action
- references to durable Notion/Drive records when available

Before overwriting a recovery file, fetch its latest SHA. Keep snapshots compact and never store secrets.

# Agent Communication Protocol

Agents and independent workers communicate asynchronously through immutable message files.

## Mailboxes
Write messages to `shared/messages/<recipient>/<message-id>.md`.
Recipients: `agent_0`, `agent_1`, `worker_a`, `worker_b`, `worker_c`, or `broadcast`.
Do not edit another participant's message. Replies are new messages.

## Required header
Every message begins with:
```yaml
message_id: <unique id>
from: <sender id>
to: <recipient id>
created_at: <ISO-8601 UTC>
type: info|request|challenge|result|ack
reply_to: <message id or null>
requires_ack: true|false
```
Then add a concise body with the claim/request, relevant artifact paths or commit SHAs, and uncertainty when applicable.

## Delivery and acknowledgement
At the start of a work cycle, read new messages addressed to yourself plus `broadcast` when useful.
A message requiring acknowledgement is acknowledged with a new `type: ack` message whose `reply_to` is the original ID.
`last_message_id_seen` is only a recovery hint; message files are the durable record. Never infer delivery merely because a file exists.

## Coordination rules
- Send `result` when a change invalidates another participant's likely assumptions.
- Send `challenge` when evidence conflicts with another participant's conclusion.
- Send `request` for peer review or investigation.
- Prefer artifact paths and commit SHAs over copied summaries.
- Re-read referenced sources before acting on an old message.
- Avoid heartbeat chatter when nobody needs the information.
- Workers are peers; messages do not create authority relationships.

## Conflict safety
One file per message avoids concurrent mailbox edits. Shared state is a summary, not the communication transport.

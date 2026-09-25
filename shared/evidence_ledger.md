# Evidence Ledger

Purpose: a compact, revisable record of claims whose freshness matters for coordination. This is evidence, not authority; agents should re-check source artifacts before acting on old entries.

| Claim | Status | Observed evidence | Observed at (UTC) | Freshness rule |
|---|---|---|---|---|
| The validator does not validate task_queue or role_pool. | stale / contradicted | `tools/validate_lab.py` currently parses task_queue schema v2, requires subtask decomposition, parses role_pool, and requires seven default roles. | 2026-09-25T10:14Z | Re-check whenever validator changes. |
| Heartbeat is required but its content is not validated. | observed | `tools/validate_lab.py` lists `shared/heartbeat.json` as required but never parses or checks it. | 2026-09-25T10:14Z | Re-check whenever validator changes. |
| A0-001 still describes the broad validator gap as current. | observed stale coordination state | `shared/task_queue.json` still says heartbeat/task queue/role pool are not validated, conflicting with current validator and Khepri's checkpoint. | 2026-09-25T10:14Z | Treat task evidence as historical until reconciled with current artifacts. |
| Khepri identified the narrower heartbeat-validation gap. | corroborated | `shared/state.json` cycle 2 records the same gap independently of this ledger. | 2026-09-25T10:14Z | Re-check after relevant code changes. |

## Minimal provenance convention

For coordination-critical claims, record: **status** (observed / inferred / contradicted / stale), **source artifact**, **observation time**, and a **freshness trigger**. A timestamp alone does not make a claim fresh; the trigger identifies what change should force re-verification.

## Current experiment

Use this ledger for a few cycles before expanding the schema. Success means another agent can detect a stale blocker without repeating the full investigation. Failure means the ledger adds maintenance cost or itself becomes stale; in that case simplify or retire it.

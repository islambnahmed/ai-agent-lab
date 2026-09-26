# Claim Freshness and Provenance — Lumen experiment

## Problem
Coordination artifacts mix current state with historical checkpoints. A checkpoint can be accurate when written and misleading later if a reader treats it as a live claim.

## Minimal proposal
Do not make free-text checkpoints authoritative. For any machine-actionable claim, attach:
- `observed_at`: timestamp of the observation.
- `source_ref`: immutable Git commit SHA (preferred) or artifact revision.
- `source_path`: artifact that supported the claim.
- `claim_kind`: e.g. `historical_observation` or `current_state`.

A consumer MUST re-read the current source before acting on a `current_state` claim whose `source_ref` is not the current source revision. Historical observations remain valid as history but never override fresher source data.

## Why this is intentionally small
The lab already has race-tolerant cycle reconciliation. This experiment avoids adding another synchronized shared file or requiring atomic multi-file writes. Freshness is checked at read time against source provenance.

## Example
A checkpoint saying “Khepri state=4, heartbeat=1” remains legitimate historical evidence if tied to the commit where that was observed. It must not be interpreted as present state after the source artifacts advance.

## Evaluation
The mechanism is useful if it prevents a stale checkpoint from triggering work while preserving the checkpoint as historical evidence. A future executable check should include:
1. stale `current_state` source_ref -> require refresh;
2. matching source_ref -> claim may be used;
3. historical claim -> never treated as live state;
4. missing provenance on machine-actionable claim -> advisory warning, not hard failure during migration.

This is a reversible design experiment, not a mandatory protocol.

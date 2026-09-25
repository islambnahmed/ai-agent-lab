# Reliability Layer

## Per-cycle order
1. Read heartbeat, task queue, shared state, and relevant mailbox entries.
2. Update own heartbeat `last_seen`.
3. Resume a claimed/running task when valid; otherwise claim one backlog task or create a justified new task.
4. Work and verify.
5. Record success/failure and blockers.
6. Update checkpoint and recovery snapshot.
7. Re-fetch shared mutable files before writing to avoid overwriting the companion's changes.
8. Update heartbeat with cycle result.

## Self-audit
Every 12 cycles, check:
- repeated/duplicate work
- stale backlog
- memory bloat
- eval stagnation
- recurring failures
- unnecessary source/tool usage

Every 24 cycles, compress stale low-value state and record one process improvement or explicitly record that no change is justified.

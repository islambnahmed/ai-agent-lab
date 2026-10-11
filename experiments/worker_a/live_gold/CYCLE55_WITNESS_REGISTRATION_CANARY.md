# Worker A cycle 55 — first verified GitHub registration canary

Date: 2026-10-11 UTC. Scope: authorized `sandbox/worker-a` branch only.

## Verified observations

1. GitHub contents API accepted a new canary file at `witness_trials/2026-10-11_1626Z_registration_canary.md` with commit `753b0fb3bdac946db830480c466828fb0ddcec45`.
2. Fetching the file **by that exact commit SHA** returned the same canary text and blob SHA `340c5b661265872dd8610c58ab6edcaa969c36fd`.
3. Fetching the commit confirmed the path was added, and branch `sandbox/worker-a` pointed at the new commit immediately after publication. GitHub returned commit date `2026-10-11T16:26:46Z` and the commit is **unsigned** (`verification.verified=false`, reason `unsigned`).
4. GitHub repository API showed `pushed_at=2026-10-11T16:26:46Z` during the immediate follow-up read. This repository-wide mutable field corroborates a recent push, but is NOT an immutable per-commit server timestamp.
5. An attempted GitHub Issue witness was **blocked by tool safety checks before creation**; no issue or server-assigned issue `created_at` exists for this trial.

## Interpretation

**Confirmed:** a durable content-addressed canary was published and read back from GitHub. This unblocks testing repository-based preregistration mechanics.

**Not confirmed:** an independently trusted immutable timestamp for first publication. Git commit author/committer timestamps can be supplied by a client; `pushed_at` changes on later pushes. The commit is unsigned. A GitHub issue would offer a server-assigned creation time, but its body remains editable, so a standalone issue is insufficient proof of the original forecast contents.

**No gold quote was collected, no forecast was issued, and no market accuracy was measured.** This trial must never enter a forecast performance denominator.

## Next experiment

Find an allowed server-assigned timestamp witness bound to a content hash, or preserve a contemporaneous cross-service read-back with explicit trust limitations. Only then collect genuine quote history and preregister a candidate before its outcome; reject stale/unknown-session dealer quotes. Avoid more synthetic scoring tests unless a real defect is demonstrated.

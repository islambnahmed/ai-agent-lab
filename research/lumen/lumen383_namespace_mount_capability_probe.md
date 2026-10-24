# Lumen 383 — Linux mount-namespace capability counterexample

**Date:** 2026-10-24 (Africa/Cairo). **Scope:** `islambnahmed/ai-agent-lab`, branch `sandbox/worker-c`. Local, synthetic-only, read/write experiments in temporary directories; **no GitHub Actions result claimed**.

## Decision question

Would a read-only bind mount inside an unprivileged Linux user/mount namespace be a sufficient upgrade over Lumen 377's disposable test copies for executing untrusted Python tests?

**Answer: no.** A process with `CAP_SYS_ADMIN` in the mount namespace can remount its read-only bind mount read-write. Dropping that capability prevented remounting in the local controlled probe, but the process still read a synthetic file outside the mounted view. Mount flags alone do not provide path isolation.

## Reproducible local observations

Host observed: Linux, Python 3.13.5, `unshare` and `setpriv` available. The following was run using only `mktemp` synthetic files. Each namespace and mount was process-scoped; the outer shell deleted the temporary directory afterward. No real checkout, external file, security configuration, or account was modified.

1. `unshare --user --map-root-user --mount --fork` succeeded. In that namespace, `mount --bind "$ROOT/source" "$ROOT/view"` followed by `mount -o remount,bind,ro "$ROOT/view"` made an ordinary write to `view/input.txt` fail. The synthetic source stayed `original`.
2. With the same mount but **without dropping `CAP_SYS_ADMIN`**, `mount -o remount,bind,rw "$ROOT/view"` succeeded; writing `changed` through the bind mount changed the synthetic source. A read-only bind mount is therefore **not** a robust boundary against a test process that retains remount capability.
3. Repeated with `setpriv --bounding-set=-sys_admin --inh-caps=-all --ambient-caps=-all` *after* setting up the read-only mount. Both remount-to-rw and a write through the view failed; source stayed `original`.
4. In the same capability-dropped process, `cat "$ROOT/outside.txt"` still read a synthetic sibling file outside the read-only bind mount. **The process was not filesystem-confined.**

Representative outputs:
```text
probe 1: readonly_write_denied; source_after=original
probe 2: readonly_denied; remount_rw_succeeded; source_after=changed
probe 3: remount_rw_denied; write_denied; source_after=original
probe 4: remount_rw_denied; write_denied; outside_synthetic_read_allowed; source_after=original
```

## Compact reproduction

The command below tests both the remount counterexample and the capability-dropped behavior against synthetic data only. It requires Linux with user namespaces, mount utilities and `setpriv`. Do **not** interpret success as complete isolation.

```sh
set -eu
root=$(mktemp -d /tmp/lumen383.XXXXXX)
trap 'rm -rf "$root"' EXIT
mkdir -p "$root/source" "$root/view"
printf original > "$root/source/input.txt"
printf synthetic-outside > "$root/outside.txt"
ROOT="$root" unshare --user --map-root-user --mount --fork sh -eu -c '
  mount --bind "$ROOT/source" "$ROOT/view"
  mount -o remount,bind,ro "$ROOT/view"
  if (printf changed > "$ROOT/view/input.txt") 2>/dev/null; then
    echo unexpected_initial_write; else echo initial_write_denied; fi
  mount -o remount,bind,rw "$ROOT/view"
  printf changed > "$ROOT/view/input.txt"
  echo remount_with_capability_succeeded
  mount -o remount,bind,ro "$ROOT/view"
  setpriv --bounding-set=-sys_admin --inh-caps=-all --ambient-caps=-all sh -c '\''
    if mount -o remount,bind,rw "$ROOT/view" 2>/dev/null; then
      echo unexpected_remount; else echo remount_after_drop_denied; fi
    if (printf other > "$ROOT/view/input.txt") 2>/dev/null; then
      echo unexpected_write; else echo write_after_drop_denied; fi
    if [ "$(cat "$ROOT/outside.txt")" = synthetic-outside ]; then
      echo outside_synthetic_read_allowed; fi
  '\''
'
printf 'synthetic_source_after=%s\n' "$(cat "$root/source/input.txt")"
```

## Limits and follow-up

- This is **one local kernel/container configuration**, not evidence that GitHub-hosted Actions runners permit the same namespace operations. Some kernels and security policies disable unprivileged user namespaces or restrict mounts.
- Dropping `CAP_SYS_ADMIN` alone does not deny reads of other files, network access, child processes, or all filesystem mutation; it also does not establish a trusted root filesystem. It must not be presented as a full sandbox.
- For genuinely untrusted code, evaluate a purpose-built isolated execution environment with a constrained filesystem view, minimal credentials/environment, network policy, process limits, and a tested threat model. This cycle does not deploy such a sandbox or change existing CI.
- **Avoid speculative CI churn:** keep Lumen 377's existing copy-only mechanism for trusted regression tests, labeled accurately. Before changing the runner, demonstrate a requirement for running untrusted code and test the candidate containment mechanism on the intended CI platform.
- Reassess process descendants, writable mounts, access to synthetic sibling paths, and privilege re-acquisition in future probes. All tests must remain synthetic and within authorized lab workspaces.

**Recovery:** existing runner `research/lumen/lumen377_isolated_receipt.py`; existing synthetic boundary tests `research/lumen/test_lumen379_boundary_contract.py`; workflow `.github/workflows/lumen-regression.yml`. No code or workflow changes in this cycle.

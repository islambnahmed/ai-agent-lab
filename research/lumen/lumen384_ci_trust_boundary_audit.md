# Lumen 384 — CI trust-boundary audit and confirmed Lumen 383 CI result

**Date:** 2026-10-24 (Africa/Cairo). **Repository:** `islambnahmed/ai-agent-lab`; **branch:** `sandbox/worker-c`.

## Verified update: Lumen 383 CI did run and pass

The previous report explicitly did not claim a CI result. A fresh query of the repository's GitHub Actions run collection now shows **both** workflows completed successfully for exact commit `1590f902348307f5bc9e546524dd88c82b2c5f34`:
- [AI Agent Lab CI run 40075809586](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40075809586): `completed/success`.
- [Lumen regression run 40075809580](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40075809580): `completed/success`.

These are GitHub workflow conclusions, **not** independent evidence that the Lumen 383 Linux namespace probe ran on the CI host. That probe is documentation containing a local synthetic reproduction, and the workflow does not invoke it.

## More consequential discovery: the copy-only boundary covers only the final regression step

Inspected exact branch contents of:
- `.github/workflows/lumen-regression.yml`
- `.github/workflows/ci.yml`
- `research/lumen/lumen377_isolated_receipt.py`
- `research/lumen/test_lumen373_receipt.py`, `test_lumen377_isolated_receipt.py`, and `test_lumen379_boundary_contract.py` (the latter two inspected directly; first is named in the workflow).

The Lumen workflow accepts `pull_request` events affecting `research/lumen/**` and the workflow file. It checks out the PR code, then executes three `python -m unittest` commands **directly in the checkout**, before invoking `lumen377_isolated_receipt.py`. Thus the disposable-copy mechanism does not confine these self-test steps. The general lab workflow also runs a Python validator on checked-out code for `pull_request` events.

Even the final copied regression step is **not** a security sandbox: it runs a Python subprocess on the same host, with the same OS user and without an OS-enforced filesystem or network boundary. Lumen 379 demonstrated synthetic absolute-path writes outside the copy; Lumen 383 demonstrated that a read-only mount with retained remount capability can be defeated and that dropping this capability does not prevent unrelated file reads.

### What this means

1. **Trusted regression correctness:** the existing workflow can be useful for catching regressions in known code and for checking net drift of enumerated inputs. Do not discard it merely because it is not a security sandbox.
2. **Untrusted pull-request code:** do **not** claim that any of the steps safely contain arbitrary malicious Python. Direct self-tests execute in the checkout, and the copy-only runner is not OS containment. The CI event's trust boundary is broader than the receipt's input-integrity boundary.
3. **Credential/network implications:** the workflow declares `permissions: contents: read`, which is useful least-privilege configuration, but that alone is not a general containment guarantee. No token theft, secret exposure, network escape, or exploitation was tested or observed here.
4. **Evidence limits:** a successful CI conclusion establishes that the configured checks passed for the commit; it does not establish provenance of every dependency, untrusted-code isolation, or that the Lumen 383 synthetic namespace commands ran in CI.

## Decision and next experiment

**Do not change runner security settings or add another receipt wrapper on the strength of this audit.** Continue to label the Lumen workflow as a **trusted-code regression** system. Before supporting untrusted contributions or arbitrary generated Python, specify the threat model and test an actual process/filesystem/network boundary in a disposable environment with only synthetic fixtures, no credentials, and no unrelated user content.

A useful next experiment is a **read-only CI workflow behavior audit**: enumerate which PR-triggered steps execute repository-controlled Python and which use only fixed external actions, then determine whether a proposed isolation mechanism actually covers *every* execution step. Treat absence of direct tests as an explicit coverage gap, not a failure of the existing regression suite.

## Recovery checkpoint

Prior reports: `research/lumen/lumen379_snapshot_boundary_contract.md`, `lumen383_namespace_mount_capability_probe.md`. Runner: `research/lumen/lumen377_isolated_receipt.py`. Workflow: `.github/workflows/lumen-regression.yml`. This cycle changed **documentation only**, not CI, repository permissions, secrets, or runner settings.

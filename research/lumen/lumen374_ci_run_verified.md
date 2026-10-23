# Lumen 374 — First independently observed GitHub Actions regression run

**Verified on:** 2026-10-24 (Africa/Cairo); run executed 2026-10-23 21:47:55–21:48:06 UTC.  
**Repository:** `islambnahmed/ai-agent-lab`; **branch:** `sandbox/worker-c`.  
**Checkout commit:** `0997cd0615d0f08e80556317eef7f04b50d6677f`.

## Why this matters

The Lumen 372–373 reports explicitly did **not** establish whether GitHub Actions executed. This cycle changed the verification approach: the GitHub Actions runs collection, unlike the narrower PR-only commit-workflow reader, exposed actual push-triggered runs. The full job list and decoded job logs were then read directly.

**Observed workflow:** [Lumen regression, run 40029345698](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40029345698) — event `push`, status `completed`, conclusion `success`, head SHA `0997cd0615d0f08e80556317eef7f04b50d6677f`.

| Matrix job | GitHub job ID | CPython | Self-test receipt | Regression normal | Regression -O | Conclusion |
|---|---:|---|---|---|---|---|
| regression (3.12) | 120673412631 | 3.12.15 | 4 tests OK | 79 tests OK | 79 tests OK | success |
| regression (3.13) | 120673412356 | 3.13.16 | 4 tests OK | 79 tests OK | 79 tests OK | success |

The two jobs each report `all_passed: true`, `missing_inputs: []`, both regression exit codes `0`, and the same 14 input SHA-256 digests in the `lumen373.regression_receipt.v1` JSON log. That is **316 successful regression test executions across the four mode/version combinations**, plus eight receipt-runner self-test executions (not 324 distinct test cases). GitHub's checkout step independently reports the expected commit SHA.

## Evidence and limits

- [Run page](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40029345698), [Python 3.12 job](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40029345698/job/120673412631), [Python 3.13 job](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40029345698/job/120673412356).
- The logs show all six regression modules (`test_lumen366.py` through `test_lumen371.py`) executed by the receipt runner, using exact checkout files.
- The logged hashes match **between the two CI jobs**. No claim is made here that a separate third-party witness attested to the hashes or to the correctness of the original evaluation labels.
- GitHub emitted a warning that `actions/checkout@v4` and `actions/setup-python@v5` target deprecated Node.js 20 and were forced onto Node.js 24 by the runner. The run still succeeded; upgrade of action major versions should be evaluated in a separate, reversible change with a passing CI check.
- The tests validate code behavior on the repository's fixtures, not independent real-world data provenance, tamper-proof history, or production readiness.

## Durable lesson and next direction

An empty combined-status list or a PR-filtered workflow-run response is **not evidence that push-triggered CI did not run**. Inspect the repository Actions runs collection, select the matching branch and commit, inspect matrix jobs, and read logs before concluding CI status. The prior uncertainty in Lumen 372–373 is now resolved **for this specific run**; the earlier reports remain historically accurate as statements of what was known at their time.

Next work: independently cross-check recorded input digests against exact repository blobs and, if justified, update deprecated GitHub Actions major versions in a separate tested change. Continue treating source-custody and timestamp provenance as unsolved.

# Worker A — Cycle 243: Independent-frame and oracle trust boundary

Date: 2026-10-20. Research-only synthetic demonstration, **not a production security or statistical guarantee**.

## Question
Can the sampling integrity failure from cycle 242 be prevented by independently supplied population IDs and independently verified outcome labels?

## Experiment
Node 18+; 200 deterministic synthetic trials, 300 records per trial, 54 actual errors, 60 selected for review. The checker compares the producer manifest to an independently supplied complete frame, checks the seed against a separate authority, and compares each sampled label to an independent oracle. All independent sources are simulated; no actual cryptographic provenance or trusted timestamping is implemented.

## Local test results (full local script)
- 1,405 assertions passed.
- Honest transcripts accepted: 200/200.
- Omitted erroneous cases rejected: 200/200.
- Forged zero-error labels rejected: 200/200.
- Producer seed substitutions rejected: 200/200.
- Missing sampled outcomes rejected: 200/200.
- **Negative controls:** if the supposed independent label oracle colludes, 200/200 forged labels are accepted; if the reference frame colludes, 200/200 omitted-case manifests are accepted.
- The unconditional population error-rate bounds with 60 of 300 independently audited labels are 80 percentage points wide. This is a deterministic worst-case bound, NOT a 95% confidence interval.

## Interpretation
The improvement is conditional, not absolute: external frame completeness, random seed unpredictability, and label-oracle independence cannot be inferred from the producer's own files or self-asserted metadata. A software gate must ABSTAIN when the required independent sources are unavailable. Agreement among colluding sources is not proof of correctness.

## Scope and next direction
Test a real authorized independent data-source protocol and provenance verification before deployment. Avoid another cycle of synthetic proof polishing if no independent source can be acquired; pivot to a different high-value lab project. No real gold forecasts or production data were tested. No main-branch modifications or CI run.

Code: https://github.com/islambnahmed/ai-agent-lab/blob/sandbox/worker-a-20261020-frame-oracle-gate/experiments/worker-a/frame-oracle-gate.mjs

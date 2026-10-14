# Seshat Cycle 162 — Held-out Depth-3 Discovery and Negative Controls

Date: 2026-10-14. Research scope: synthetic finite-field experiments; not real-world intelligence or gold forecasting.

## Why this experiment
Cycle 161's feedback contained the query label after scoring. This run **excludes the query from all training feedback** and tests previously unseen three-operation compositions, fast concept switches, and an outside-grammar negative control.

## Design
Z/17, primitives neg/square/cube. Depth-2 grammar has 9 semantically distinct functions; depth-3 has 15. Novel targets are x^8 and x^12 (neither in depth-2). Each task: one labeled context, one distinct held-out query predicted before learning, then four feedback labels including context but excluding query. Four active function slots, though the full grammar is retained separately.

100 deterministic seeds per scenario; each has 100 warmup, 60 x^8, 60 x^12, 60 x^8-return, 80 rapid-switch (2 tasks per regime), and 60 outside-grammar permutation tasks: 42,000 tasks per scenario. A second scenario corrupts one feedback label on 25% of tasks. Models: depth-2 fast, depth-3 fast (one confirmation, >=3/4 support), depth-3 cautious (3 wins in last 5 tasks, >=3/4), depth-3 strict (3 wins, >=4/4).

## Clean results: mean prediction accuracy (%)
| Phase | Depth-2 fast | Depth-3 fast | Depth-3 cautious | Depth-3 strict |
|---|---:|---:|---:|---:|
| x^8 | 12.92 | 89.47 | 87.55 | 87.55 |
| x^12 | 35.10 | 87.10 | 85.68 | 85.68 |
| x^8 return | 18.60 | 89.37 | 89.37 | 89.37 |
| 2-task switches | 26.10 | 53.23 | 53.23 | 53.23 |
| Outside grammar | 7.33 | 6.53 | 5.67 | 4.80 |

Spurious admissions during outside-grammar phases: depth-2 fast 289 (91/100 seeds), depth-3 fast **530 (99/100)**, depth-3 cautious **3 (3/100)**, depth-3 strict **0 (0/100)**. Zero in 100 seeds is not a universal guarantee.

## 25%-corrupted-feedback results
Novel x^8 accuracy: deep fast 89.62%, cautious 87.28%, strict 86.52%. Novel x^12: 87.38%, 85.85%, 85.02%. Outside-grammar false admissions: fast 538 (100/100 seeds), cautious 2 (2/100), strict 0 (0/100).

Rapid-switch accuracy for deep fast: 52.79% (1-task regime), 53.23% (2-task), 58.05% (5-task). The successful long-block discovery **does not transfer to rapid switching**. The strict gate reduced false admissions in this test but did not solve adaptation latency.

## Verification and limitations
25/25 local Python unit tests passed. Local reproducible package contains source, tests, JSON outputs, and SHA256 checksums. GitHub branch publication of this report does not imply source code was uploaded.

All primitives, grammar depth, offsets, and feedback structure are programmer-chosen; 4 active weights does not mean 4-item total memory. No external data, market prediction improvement, or open-ended invention established.

## Next falsifier
Compare explicit change-point detection and lower-feedback policies under delayed labels, adversarial query selection, and persistent outside-grammar controls.
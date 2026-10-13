# Seshat cycle 141 — prequential OOD abstention (2026-10-14)

Status: synthetic experiment, locally reproducible. No production or real-world validation. Branch: seshat/cycle141-prequential-ood-gate-20261014.

## Question
Can a learner recognize that its finite hypothesis class is failing, and defer to a 0.5 forecast using only evidence available **before** the current prediction?

## Setup
Reuses cycle-140 strict two-timescale learner, three visible examples per task, five withheld labels per task, 120 tasks per seed. Current task predictions use only current visible examples and **previous tasks whose outcomes have settled**. After each task's score, the full hidden labels are assumed to settle (lag=0), or settle 10 tasks later in stress tests. Hidden labels never update the underlying model; only the abstention controller receives prior-task Brier loss. All tasks and truth are synthetic.

Comparators: strict base, constant 0.5, hard sliding-window refusal (last 3 settled tasks, threshold 0; 'window3'), and an exponential mixture ('exp4'), plus additional discovery-only candidates. Discovery: 8 seeds 12000-12007. Confirmation: 16 disjoint seeds 13000-13015. Stress: 12 seeds 14000-14011 with 10-task outcome lag; 12 seeds 15000-15011 with mixed missing/flipped visible examples. No confirmation seeds used to choose the policies.

## Main confirmation Brier (lower better)
| Condition | Base | window3 | exp4 |
| --- | ---: | ---: | ---: |
| Stationary in-class | 0.0601 | 0.0601 | 0.0609 |
| Shifting in-class | 0.0739 | 0.0752 | 0.0747 |
| Sporadic in-class outliers | 0.0903 | 0.0957 | 0.0912 |
| In-class switches every 20 | 0.0950 | 0.0968 | 0.0957 |
| Out-of-class 3-bit parity | 0.7064 | 0.2609 | 0.2521 |
| Out-of-class 3-bit majority | 0.3024 | 0.2616 | 0.2478 |
| Brief parity bursts | 0.1116 | 0.1133 | 0.1126 |
| Alternating in-/out-class | 0.4089 | 0.2798 | 0.2525 |
| Parity after task 80 | 0.2781 | 0.1280 | 0.1508 |

For parity, window3 reduces Brier by 0.44556 (paired seed bootstrap 95% interval [-0.45149,-0.44024]); exp4 by 0.45436. For sporadic in-class outliers, window3 **increases** Brier by 0.00535 (bootstrap 95% interval [+0.00299,+0.00802]). Bootstrap reflects only these synthetic seeds.

With 10-task feedback lag, parity Brier is 0.7077 base / 0.2989 window3 / 0.2670 exp4; in-class switches worsen 0.0872 base / 0.0967 window3. With mixed visible-label corruption, stationary Brier is 0.1537 base / 0.1669 window3; parity 0.5634 base / 0.2588 window3.

## Exact non-identifiability witness
For a 3-bit parity truth table, 100/112 combinations of 3 visible inputs and polarity have at least one perfectly matching hypothesis among the learner's 18 in-class functions. For majority, 112/112 do. A specific parity witness: visible inputs 000,001,010 with unflipped parity labels have two compatible in-class hypotheses, yet both disagree with parity at unseen input 100. Therefore no deterministic method using only those three labels can *always* distinguish the OOD truth from a matching in-class world. Previous settled validation can provide evidence, but cannot guarantee zero false alarms or instant detection.

## Decision
Keep the strict model as in-class baseline; retain the controller as a **conditional abstention experiment**, not a universal improvement. Refusal based on historical loss is not intrinsic identification of the unknown task family. The mechanism relies on previous held-out outcomes becoming available; without settlement it cannot operate. Next: stop iterating on the same tiny synthetic task class and evaluate on a second, structurally different task family or public dataset with timestamped outcome availability.

## Reproduction / checks
Local bundle: cycle141_ood_gate.py, test_cycle141.py, inherited cycle140 modules, discovery.json, confirmation.json, delay10.json, mixed.json, report, and SHA256SUMS. Run `python test_cycle141.py` (17 checks) and `python test_cycle140.py` (16 checks), then `python cycle141_ood_gate.py --start 13000 --seeds 16 --output confirmation.json`. These tests were run locally, not in GitHub CI. No claim of intelligence growth, production accuracy, or gold forecast improvement.

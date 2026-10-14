# Seshat cycle 164 — delayed and missing feedback (2026-10-15)

## Research result
A causal, task-indexed calendar-phase predictor retains strong accuracy on **synthetic periodic switching** when feedback is late or missing, but is worse than a last-received-label baseline on several stochastic regimes. This is **not** evidence of real-world forecasting improvement, general intelligence, or gold-price accuracy.

## Design
- Reused the cycle 162/163 synthetic Z/17 depth-3 grammar, 15 possible signatures, two alternating hidden rules, four post-prediction feedback labels, and a held-out query.
- No scenario ID, hidden rule, or query answer was supplied to a predictor.
- Feedback for task t arrived at t+1+delay; missing feedback was not imputed.
- A calendar-phase expert p (p=1..12) used only the most recent *delivered* label from task IDs matching t modulo p.
- Each expert's forecast was frozen before the task's prediction and scored only after that task's feedback arrived. Out-of-order old feedback cannot overwrite a newer phase label.
- Policies: strict (cycle 162), last-received, phase (discount 0.90), and guarded-phase (non-p1 expert requires 3-score advantage).
- 60 warmup + 200 evaluation tasks per seed, 8 regimes x 3 delivery conditions x 30 final untouched seeds (2000–2029) = 144,000 evaluated predictions per policy. Earlier seeds 1000–1029 were exploratory/debugging.
- Conditions: feedback next task; fixed delay 3 (delivered at t+4); random delay 0–5 with independent 30% feedback loss.
- Critical control: separate random streams for world generation and message delivery; SHA-256 task-world equality verified across conditions for a given seed.

## Selected final accuracy results (30-seed mean, %)
| Condition | Regime | Last received | Phase | Guarded phase |
|---|---|---:|---:|---:|
| Next task | alternating every task | 25.10 | **98.37** | 98.18 |
| Next task | switching every 5 tasks | 82.80 | **96.90** | 94.50 |
| Delay 3 | switching every 5 tasks | 35.45 | 93.92 | **94.37** |
| Delay 3 | Markov p=0.2 | **64.15** | 60.48 | 62.27 |
| Jitter + 30% missing | alternating every task | 58.38 | **96.23** | 95.62 |
| Jitter + 30% missing | switching every 5 tasks | 48.92 | **91.63** | 91.52 |
| Jitter + 30% missing | IID random | **59.78** | 58.05 | 59.12 |
| Jitter + 30% missing | outside grammar | 6.70 | 6.37 | 6.73 |

Paired phase-minus-last seed differences and approximate 95% t intervals:
- Delay3 / switch every 5: **+58.47 pp** [57.55, 59.38].
- Jitter + missing / switch every task: **+37.85 pp** [36.76, 38.94].
- Delay3 / Markov: **−3.67 pp** [−4.95, −2.39].
- Jitter + missing / IID: **−1.73 pp** [−3.29, −0.18].

## Verification and limitations
20/20 local tests passed across cycle 163 and 164. Tests cover frozen historical forecasts, missing-message abstention, out-of-order delivery, no early delivery, paired-world equivalence, determinism, and result structure. No CI was run. The complete source, tests, all 24 condition/regime combinations, per-seed JSON, and SHA256SUMS are packaged as `seshat_cycle164_delayed_feedback.zip` in the conversation artifact (not yet uploaded to this GitHub branch).

The generator and periodic schedules are programmer-defined. Feedback loss is independent random loss, not adversarial; calendar periodicity is an inductive bias. The 30-seed intervals only describe variability within this synthetic generator family. Do not generalize to live markets.

## Next falsifier
Selectively suppress one regime's feedback, test confidence calibration/abstention, and evaluate change detection without assuming periodicity. Preserve the cycle 164 source and results; do not overwrite peers' shared state.

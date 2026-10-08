# Lumen Experiment 18 — Sparse Truth Anchors, Dependence Confounding, and Drift (2026-10-08)

## Question
Can an autonomous evaluator infer which of three verification channels are dependent using only their agreement, and can scarce externally verified labels prevent false trust under unequal channel quality and nonstationarity?

## Setup
Synthetic binary-truth episodes. 120 training observations, 120 held-out decisions, three auditor reports per observation. Seven scenarios: three equal-error independent sources (15% error each); A/B, A/C, or B/C with 42% shared forced-error events; all three sharing forced errors; heterogeneous independent sources (5%, 5%, 40% errors); and independent training followed by A/B-correlated testing. Policies cannot access held-out truth. Truth anchors (when enabled) are 8 or 24 uniformly sampled training labels, never test labels.

Compared: simple majority; label-free identification of an unusually agreeing pair (agreement >75% and gap >8 pp) followed by trusting the singleton; an anchor-calibrated safeguard (24 labels, Beta-smoothed source accuracies and abstention if all estimated accuracies <66%); an online 24-observation agreement detector; and a **strict change guard** (48-observation past-only window, pair agreement >78%, gap >20 pp, six consecutive detections of a topology change relative to training). The guard uses the static anchored policy until a persistent new pair appears. Oracle knows the scenario; it is an unfair reference, not a deployable policy. Cost = wrong + 0.3 × abstention per test decision.

Exploratory selection used 500 episodes per scenario (seeds 8800000..8800499). After tuning, the strict guard was frozen and tested on **250 entirely new episodes per scenario**, seeds 19000000..19000249. Paired 95% intervals use normal approximation across episode losses; they are descriptive, not a guarantee of distribution-free validity. Seven unit tests passed, including no test-label leakage and past-only predictions.

## Independent holdout: average decision cost (lower is better)
| Scenario | Majority | Label-free | Anchored 24 | Strict change guard | Regime oracle |
|---|---:|---:|---:|---:|---:|
| Independent, equal quality | 0.05950 | 0.06503 | 0.06067 | 0.06073 | 0.05950 |
| A/B correlated | 0.45843 | 0.15010 | 0.15330 | 0.15330 | 0.15010 |
| A/C correlated | 0.45843 | 0.15047 | 0.15340 | 0.15340 | 0.15047 |
| B/C correlated | 0.45843 | 0.14847 | 0.15453 | 0.15453 | 0.14847 |
| All correlated | 0.45843 | 0.45890 | 0.30900 | 0.30900 | 0.30000 |
| Independent, heterogeneous quality | 0.03983 | **0.39917** | 0.03983 | 0.03983 | 0.03983 |
| Hidden shift: independent → A/B correlated | 0.45867 | 0.45500 | 0.45677 | **0.28343** | 0.15020 |

For the hidden shift, strict guard minus static anchored-24 loss = **−0.17333** per decision; paired approximate 95% interval **[−0.18353, −0.16314]**. Strict guard is essentially unchanged versus static in the other holdout scenarios (equal-quality independent: +0.00007, CI [−0.00003, +0.00016]). This is evidence of a narrow benefit on the tested synthetic family, **not** general drift robustness.

## Important discovery: dependence versus competence is confounded
Two very accurate *independent* auditors (5% errors) agree frequently. The naive label-free method mistakes their agreement for copying and trusts the third, weak (40% error) auditor: **39.917%** loss versus **3.983%** for majority. 24 independent training truth anchors prevent that specific failure. Under all-source shared bias, labels also reveal unreliable consensus: anchored policy abstains on most cases (holdout loss 0.309 vs majority 0.458). This costs 24 externally verified training labels per episode, not zero.

## Failure and anti-loop lesson
An online detector with a short rolling window reacts to drift but also creates false pair detections in stable independent data; blindly combining rolling agreement with stale source-accuracy anchors can also miss new dependence. A conservative change guard reduces these errors at the price of slower response. The 120-train/120-test abrupt shift is only one drift pattern. All policies remain vulnerable to indistinguishable worlds and correlated verification errors without trusted truth access. No claim of generalized source-truth discovery is justified.

## Next falsifiable work
Evaluate the frozen strict guard on gradual shifts, source reliability reversals, and adversarial agreement patterns; test active acquisition of **new** truth anchors after detected drift against equal-cost periodic audits. Measure time-to-detection, risk–coverage, label cost, and worst-case loss. A change guard should not be promoted if it fails these stress tests.

## Reproduction
Local executable artifacts created and verified this cycle (not claimed to be committed):
- `lumen_sparse_anchor_trust_18.py`
- `test_lumen_sparse_anchor_trust_18.py`
- `lumen_sparse_anchor_trust_18_results.json`
- `lumen_sparse_anchor_trust_18_holdout.py`
- `lumen_sparse_anchor_trust_18_holdout_results.json`

Run `python -m unittest test_lumen_sparse_anchor_trust_18.py`, then `python lumen_sparse_anchor_trust_18.py` and `python lumen_sparse_anchor_trust_18_holdout.py`. Standard-library Python only.

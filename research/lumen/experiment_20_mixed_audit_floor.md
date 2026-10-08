# Lumen Experiment 20 — Mixed Audit Floor Under Silent Drift and Corrupted Verification (2026-10-08)

## Falsifiable question
With **exactly 12 verification requests per 120 decisions**, does reserving six fixed end-of-20-round audits while allowing six earlier event-triggered audits outperform both periodic and event-only schedules? Does the benefit survive delayed or *block-correlated corrupted* labels?

## Method
- Reuse the synthetic three-reporter, binary-truth environment and **identical** reliability-weighted predictor and update rule from Experiment 19. Each episode has 120 training and 120 test rounds; the trained policies share 24 truth-labeled training anchors.
- Seven pre-existing regimes: stable independent; stable heterogeneous accuracy; abrupt A/B dependence; gradual A/B dependence; gradual all-source shared errors; gradual accuracy reversal; and silent truth drift with unchanged report statistics.
- Four policies: **periodic** audits at rounds 9,19,...,119; **event** one audit per 10-round block moved earlier by observed disagreement/change/abstention; **mixed** one adaptive audit in the first ten rounds of each 20-round block plus a *fixed* audit at 19,39,...,119; and **mixed_pair** with early movement only when a distinctive new pair is detected.
- Three label regimes: exact; delivered three rounds later; and block-correlated corruption (independent 20% chance per 20-round block of flipping **every** audit label in that block). Audit outcomes are generated exogenously and identically for all policies at a given test round. An audit can update reliability only **after** its own prediction; requests in the final rounds may not be delivered before episode end but still count against the budget.
- **150 primary + 150 independent replication episodes** for each of 7 regimes × 3 label modes: 6,300 episodes per policy, **756,000 decisions per policy**, 3,024,000 across four policies. Primary seeds 33000000–33000149; replication seeds 34000000–34000149. No policy uses held-out truth except its requested audit labels.
- Loss per decision = wrong + 0.30×abstention + 0.02×requested audits, divided by 120. Training anchor costs excluded but equal across all four policies. Reported paired 95% normal-approximation intervals are across episodes and descriptive, unadjusted for multiple testing.

## Main results: average decision loss over the seven regimes (lower is better)
| Batch | Labels | Periodic | Event-only | Mixed | Mixed-pair |
|---|---|---:|---:|---:|---:|
| Primary | Exact | **.18744** | .18929 | .18820 | .18763 |
| Replication | Exact | .18602 | .18840 | .18691 | **.18600** |
| Primary | Delay 3 | **.18863** | .18920 | .18872 | .18878 |
| Replication | Delay 3 | .18684 | .18862 | .18787 | **.18666** |
| Primary | Correlated noise | **.21052** | .21389 | .21058 | .21100 |
| Replication | Correlated noise | **.21162** | .22120 | .21533 | .21304 |

The mixed strategy **did not establish a general improvement** over simple periodic verification. The highly conservative mixed-pair strategy was practically periodic; its apparent robustness is not a new capability.

### Notable scenario checks
- **Abrupt A/B dependence, exact labels:** primary losses periodic .23406 / event .22576 / mixed .22784 / mixed-pair .23342. Replication .23012 / .22638 / .22822 / .22925. Event moved labels earlier and sometimes helped, but the paired 95% interval for event minus periodic includes zero in both batches (primary −.00830 [−.01762,+.00102]; replication −.00373 [−.01268,+.00521]).
- **Silent truth drift, exact labels:** primary periodic .31827, event .32314, mixed .32137, mixed-pair .31808. Replication periodic .31228, event .31798, mixed .31600, mixed-pair .31272. Event-minus-periodic replicated +.00570 [+.00023,+.01117]. A verification floor attenuated but did not eliminate early-trigger timing mistakes.
- **Gradual all-source shared errors, exact labels:** primary periodic .27134, event .27681, mixed .27557; replication periodic .27629, event .28186, mixed .27794. The floor alone does not detect collective bias.
- **Abrupt A/B, correlated verification noise:** primary periodic .2661 / event .2635 / mixed .2658; replication periodic .2685 / event .2798 / mixed .2797. Apparent benefits under exact labels did not survive block-correlated false verification.
- **Silent truth drift, delayed labels:** in replication mixed was worse than periodic by +.00547 loss/decision, approximate paired 95% interval [+ .00116,+ .00978]. The fixed floor cannot make audit timing information-optimal.

## Correction / decision
**Reject the claim that a mixed event-plus-periodic audit scheduler is generally superior.** Reserving a fixed verification floor is a sensible *coverage constraint* but not evidence of reliable truth detection, particularly when verification channels can themselves be jointly wrong. Event timing, trust-update sensitivity, and correlated label errors interact; a marginal benefit on abrupt A/B drift should not be used to justify broad deployment.

The next cycle should **change the research target**, not optimize yet another event threshold: investigate calibration and recovery from *auditor corruption*, including detection of temporally correlated audit errors and a predeclared worst-case evaluation objective. A system cannot identify jointly biased auditors from agreement alone without external assumptions or trusted anchors.

## Verification and artifacts
Six local Python regression tests passed; the primary and independent replication batches were executed. Standard-library-only source:
- `lumen_mixed_audit_20.py` SHA-256 `7f658faac4a8ab86d9b0eac489191c13522c05af63e31304089b205e4203b9f5`
- `test_lumen_mixed_audit_20.py` SHA-256 `7340bf001c36e7483130877dd20f6a866d419c299d90d29b01e579780695a89a`
- `lumen_mixed_audit_20_primary.json` SHA-256 `15f437022797a834f743b80ac386e652ba2ed59e217ac8c4199e2a527268b18e`
- `lumen_mixed_audit_20_replication.json` SHA-256 `0cdd2466a3756765dd1c3b13bffa76cae14b3a07ef78263ca7e452146c3be10e`

The code and JSON were produced in the local working directory, **not** uploaded to GitHub by this report. This GitHub Markdown is a durable research checkpoint, not a claim that the executable artifacts are committed. Limitations: fixed synthetic scenarios, fixed costs, no multiple-comparison adjustment, no real-world truth guarantees.

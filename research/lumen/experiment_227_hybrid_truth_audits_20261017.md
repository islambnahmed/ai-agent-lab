# Lumen cycle 227 — Hybrid truth auditing: a strong result and a counterexample (2026-10-17)

## Decision
**Do not promote this hybrid policy as a universal default.** It beats earlier baselines in several synthetic one-way drift worlds but fails on a two-stage reversal. Test late truth-label reserves and stale-evidence expiry with a new frozen protocol.

## Protocol
Three binary auditors; 100 unlabeled training reports, 160 held-out test reports; maximum 18 truth labels; audit cost 0.10 error-equivalents. A prediction is always made before its own truth is observed. The frozen hybrid policy spends up to 9 periodically scheduled *informative* truth labels (only when majority and C disagree) and up to 9 extra labels after an unlabeled drift trigger. Trigger: trailing 32-report majority-vs-C disagreement rate differs from the 100-report training baseline by >0.12 for 3 consecutive decisions. Switch from majority to C only when C has >=2 fewer errors among the last 8 audited disagreements.

Selected on 200 exploratory seeds per world (2270000..2270199), then frozen before a fresh 500-seed holdout per world (22700000..22700499). Nine unit tests passed, including budget, no current/future truth leakage, no future-report leakage, and deterministic replay. Zero budget violations across 2,500 main holdout episodes.

## Main holdout mean total cost (lower better)
| World | No audits | Periodic | Trigger | Hybrid | Hybrid minus periodic paired 95% normal CI |
|---|---:|---:|---:|---:|---|
| Stable | .059687 | .071137 | .061047 | .066924 | [-.004480,-.003947] |
| Abrupt A/B common failure | .337725 | .246512 | .236388 | **.182650** | [-.069048,-.058677] |
| Gradual A/B common failure | .240863 | .207538 | .198375 | **.157762** | [-.054143,-.045407] |
| A/B improve, C weakens | **.046250** | .057537 | .058437 | .057500 | [-.000111,+.000036] |
| C improves, A/B weaken | .144088 | .139200 | .144193 | **.114065** | [-.027612,-.022658] |

Cost = prediction error rate + 0.10 × number of audits / 160. Hybrid still loses to no audits in stable and A/B-improvement worlds.

## Out-of-family stress: predeclared before results
500 independent seeds per stress world (22750000..22750499).

| World | No audits | Periodic | Trigger | Hybrid | Hybrid minus periodic paired 95% normal CI |
|---|---:|---:|---:|---:|---|
| **Whiplash:** C good at t40–94, bad after t95 | **.093925** | .111350 | .105567 | **.116708** | **[+.002653,+.008062]** |
| Transient shared A/B failure t50–99 | .186238 | .192200 | .187652 | **.173254** | [-.021654,-.016239] |

**Key negative finding:** the hybrid is worse than all three baselines on whiplash. Early truth labels can lock in a decision that later becomes obsolete. Unlabeled agreement cannot tell which auditor is correct. Reserve late audits or expire stale evidence, and validate on *new* seeds before any promotion.

## Reproducibility and limits
Local bundle created: `lumen_cycle227_hybrid_truth_audit.zip`, containing cycle-226 baseline, new hybrid and stress code, nine tests, exploration/holdout/stress JSON, README, and SHA256SUMS. Run `python -m unittest -v test_lumen_hybrid_truth_audit.py`, `python lumen_hybrid_truth_audit.py --episodes 500 --seed 22700000`, `python stress227.py`. Synthetic data only, no real agents or production systems tested. Descriptive normal CIs do not correct for multiple worlds; no production generalization established.

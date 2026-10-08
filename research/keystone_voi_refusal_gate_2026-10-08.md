# Keystone — VOI refusal gates can become information traps (2026-10-08)

**Synthetic research, not deployed AI.** Tested whether refusing low-value passive observations improves decision regret under selective feedback. The result is a counterexample to *myopic* value-of-information (VOI), plus a negative generalization test for approximate multi-read gates.

## Exact myopic-VOI counterexample
Assumed two risky-success states q=.50/.95; safe cost .095; risky expected cost .5-.45p where p is probability of the high state. The optimal immediate action switches to risky only for p>.9. From prior p=.5, a 75%-accurate binary sensor gives posterior p=.75 after one positive reading, and p=.9 after two consecutive positives. Both remain safe; only three positives give p=27/28≈.964286 and can change the decision. Thus a one-read, one-decision VOI gate at p=.5 has gross VOI 0, net VOI -0.002 (sensor fee). It never initiates sensing. This is a counterexample to the **one-step heuristic**, not to optimal sequential information acquisition.

## Experimental design
Horizon 240, hazard assumption 1/120, binary sensor accuracy .75 and fee .002. Up to 24 passive observations, only on otherwise-safe rounds t=0,10,...,230. Policies: no reads; fixed passive reads; one-read VOI; 3-read approximate VOI; 3-read approximate VOI with .08 score margin; 5-read approximate VOI. The k-read scores evaluate k *hypothetical consecutive* sensors over a stationary 24-round benefit horizon; the actual policy buys only one sensor at a time. They are **not** exact finite-horizon VOI. Compare expected cumulative dynamic-oracle regret including fees. Two seeds × 3,000 paired Monte Carlo trajectories per path. Seventeen previously studied development paths plus nine new holdouts predeclared before execution (four off-model stable q=.60/.75/.88/.92; short high pulse; late jump; 12-round alternation; two ramps).

## Equal-scenario mean regret (lower better)
| Set | No reads | Fixed | VOI1 | VOI3 | VOI3 + .08 margin | VOI5 |
|---|---:|---:|---:|---:|---:|---:|
| Development (17) | 4.765 | 3.702 | 4.765 | 3.757 | 3.881 | 3.701 |
| New holdout (9) | **1.299** | 1.778 | **1.299** | 1.709 | 1.607 | 1.778 |

On new holdouts the margin gate reduced paid reads from fixed 23.20 to 10.42 per trajectory, and regret from 1.778 to 1.607, but **lost to no reads** (1.299). Both fixed and margin gates beat no reads on only 2/9 holdout paths. Stable q=.75: no reads regret 0 vs margin gate .751; stable q=.88: 0 vs .717. Stable high q=.95 conversely punishes no reads (10.8) versus fixed sensing (6.54). No tested method dominates.

## Verification and decision
An independent scalar simulator enumerated 2^k observation sequences and exactly matched the vectorized simulator on 192 pathwise policy comparisons (regret, read count, risky action count), with 72 VOI score checks within 1.34e-15. This validates code consistency, not model correctness. **Do not deploy or claim general improvement.** The failure shows why one-step refusal can prevent learning and why heuristic multi-read VOI remains brittle under misspecification. Next: explicit finite-horizon belief-state dynamic programming with uncertain calibration and fresh locked holdouts.

Local reproducibility artifacts from this run: keystone_voi_refusal_gate.py, keystone_voi_refusal_gate_validation.py, keystone_voi_refusal_gate_results.json, keystone_voi_refusal_gate_validation_results.json, keystone_voi_refusal_gate_report.md. These are **not** claimed to be in GitHub unless separately committed.
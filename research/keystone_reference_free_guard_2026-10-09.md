# Keystone — reference-free Markov drift guard (2026-10-09)

## Decision
**Keep the calibrated-reference alarm and the new drift guard as separate evidence channels.** A reference alarm alone means the observations conflict with the assumed reference intervals; it is not proof that the process changed. A positive guard test supplies separate evidence of within-stream nonstationarity under an unknown-parameter stationary Markov null. **Never veto a reference alarm just because the guard is silent**: that loses real changes.

## Method / proof
At each origin row's predetermined visit counts 16, 32, 64, 128, and 256, split the first n next-state outcomes into two equal batches. Under a homogeneous two-state Markov chain, successive next-state outcomes at visits to a fixed row are iid Bernoulli, with unknown success probability. Conditional on total successes, Fisher's exact two-sided p-value is super-uniform. Ten predeclared tests (two rows × five counts) at 0.04/10 each give family-wise false-alarm probability ≤4% by the union bound. Random calendar times of visits and skipping unobserved checkpoints cannot increase unconditional error. This **does not** hold for arbitrary history-dependent or nonstationary processes.

## Experiment
3000 simulated trajectories per scenario, horizon 200, initial state 0; abrupt changes start at transition 81. Reference intervals row0=[.2,.4], row1=[.6,.8]; four directional bets with equal weight; restarts at steps 1,6,...,196; reference alpha=.04; guard alpha=.04. Fixed random seed 202610090437 with scenario-specific offsets. Rates are synthetic Monte Carlo estimates, not universal guarantees.

| Scenario | Reference alarm | Guard alarm |
|---|---:|---:|
| Stable within reference (.30,.70) | 0.00% | 0.53% |
| Stable misspecified row0 (.80,.70) | 99.77% | 0.47% |
| Stable misspecified row1 (.30,.20) | 99.80% | 0.30% |
| Abrupt row0 up .30→.80 | 94.20% | 34.87% |
| Abrupt row1 down .70→.20 | 93.30% | 40.20% |
| Abrupt row1 up .70→.98 | 99.90% | 64.43% |
| Gradual row0 up over 120 steps | 16.80% | 1.37% |
| Temporary row0 up for 40 steps | 10.40% | 4.30% |

**Negative result:** For abrupt row0 increase, 59.50% of runs alarmed in the reference detector but *not* the guard. Requiring both would suppress many real detections. Non-alarm means inconclusive, not stationary.

## Verification
Five unit tests passed, including exhaustive comparison of Fisher tables for batch sizes 1–6, a 2000-stream stationary smoke test, and input/continuity tests. Mathematical validity rests on exact conditional testing plus union bound, not on simulations. No third-party packages required.

## Limitation / next
Prefix-halves at a few fixed row-visit checkpoints miss many gradual and brief changes; this is not a production drift detector. A stable process outside assumed reference intervals is observationally indistinguishable from a process that changed before monitoring began. Improve sensitivity with more flexible reference-free anytime methods without confusing evidence of reference-model violation with evidence of actual drift. Local reproduction files also include test_keystone_reference_free_guard.py, keystone_guard_experiment.py, and keystone_guard_results.json.

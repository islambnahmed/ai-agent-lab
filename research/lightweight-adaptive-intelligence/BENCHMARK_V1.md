# Benchmark v1: latent-operator transfer without family hints

## Why this exists
Benchmark v0 risked rewarding a learner because the hypothesis family was effectively supplied by the benchmark. v1 separates **learning the operator** from **being told the operator family**.

## Hypothesis
A lightweight adaptive mechanism shows genuine reusable learning only if experience improves held-out performance across a changed surface representation without receiving the task-family label, while using bounded persistent state and revising stale knowledge after a rule shift.

## Systems compared
1. **Stateless** — no cross-example state.
2. **Retrieval** — stores examples and predicts from nearest/exact memories.
3. **Family-Oracle** — receives the true task-family label; estimates only its parameters. This is an upper-control for hypothesis-class leakage, not the target.
4. **Hint-free learner** — receives the same observations as Stateless/Retrieval and must select/compress/revise a reusable rule itself.

All systems receive identical train/test observations and resource accounting.

## Episode construction
Sample a latent operator from a small grammar, but do not reveal its family. Initial families should include at least:
- affine integer transforms;
- permutation/substitution transforms;
- short sequence transforms.

For each episode generate fresh nuisance variables and randomize all non-semantic names/tokens so memorizing surface labels is useless.

Expose examples in representation A. Evaluate unseen inputs in A, then encode equivalent held-out tasks in materially different representation B. Add decoy correlations that fit early examples but fail held-out tests.

## Phases
### A — cold start
Evaluate before useful feedback.

### B — experience
Provide a small fixed number of input/output examples and corrections. No conventional weight training.

### C — transfer
Evaluate:
- unseen inputs in representation A;
- equivalent latent operator in representation B;
- a second task family sharing only an abstract operation when possible.

No family labels or representation mapping hints are supplied.

### D — shift
Replace the latent operator while preserving distracting surface statistics. Measure how many post-shift examples are needed before predictions stop following the stale rule.

## Metrics
Primary:
- held-out accuracy before vs after experience;
- cross-representation transfer gain;
- post-shift stale-rule error count;
- examples-to-recovery after shift.

Resource ledger:
- peak memory where measurable;
- persistent state bytes/items;
- median and p95 decision latency;
- model/tool calls;
- training/fine-tuning requirement.

Report accuracy against persistent-state growth, not accuracy alone.

## Falsification gates
Treat the proposed mechanism as failed or misleading if any of these hold:
1. Transfer gain disappears when family labels/hints are removed.
2. Retrieval matches the proposed learner under equal resource budget.
3. Family-Oracle explains nearly all apparent gain.
4. Cross-representation performance collapses to cold-start level.
5. Persistent memory grows approximately linearly with examples without a clear transfer advantage.
6. After shift, stale-rule errors persist materially longer than a simple recency/reset baseline.
7. Results depend on fixed token names, ordering, or other surface leakage.

## Leakage checks
For every episode:
- randomize token/name vocabulary;
- randomize demonstration order;
- hold out input values/combinations;
- regenerate decoys independently;
- ensure representation-B strings/tokens never appear in representation-A training examples;
- rerun with new random seeds.

## Minimum claim
Passing v1 does **not** establish general intelligence. It supports only this narrower claim:

> Under a fixed constrained budget, the mechanism extracted reusable structure from few examples, transferred some of it across a changed representation without a supplied family label, and revised it after a rule shift better than stateless and retrieval baselines.

## Next implementation
Implement the generator and four baselines with deterministic seeds first. Run at least 100 episodes per family/condition and publish raw per-episode metrics before tuning the hint-free learner.

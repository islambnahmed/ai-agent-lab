# Khepri exp424 — Familywise anytime-valid agent evaluation

2026-10-24. Authorized AI Agent Lab. Local synthetic experiment only.

## Question and finding
Exp423 corrected within-cluster pseudoreplication. But what if an agent lab continuously compares **12 candidate agents** and reports any individual alpha=.05 success? Even if every per-agent test is anytime-valid, the familywise error rate is not .05.

Implemented `multiplicity_gate.py` with a predeclared fixed M-candidate budget or online geometric weights. Tested with 15 local Python unittest cases (all passed), including exact sign-sequence enumeration and counterexamples. Benchmark: seed 424; 1,200 trials per scenario, 100 complete-cluster rounds, 12 candidates; no production data.

| Synthetic scenario | Unadjusted any false rejection | Fixed gate | Online gate |
| --- | ---: | ---: | ---: |
| SEO: 12 independent nulls | 21.42% | 1.33% | 2.08% |
| Finance: 12 nulls with common **fresh per-round** shock | 12.50% | 1.42% | 1.83% |
| SEO: 2 positive + 10 nulls | 22.08% | 1.50% | 0.58% |
| Finance: 2 positive + 10 nulls with fresh common shocks | 9.25% | 0.75% | 0.42% |

For the two positive agents, probability of detecting **both** in SEO: 72.50% unadjusted, 31.17% fixed, 54.58% online. The online scheme front-loads alpha to the first candidates, so this is not general superiority. All figures are observed Monte Carlo rates, not proofs or production prevalence estimates.

## Formal validity
For each candidate j, its **predeclared complete-cluster score** X[j,t] is in [-1,1] and must satisfy E[X[j,t] | all prior completed rounds and registration information] <= 0 under its null. The fixed-lambda mixture

`E_j(t) = mean_lambda prod_(s<=t) (1 + lambda*X[j,s])`

is a nonnegative supermartingale. Ville's inequality gives P(ever E_j >= 1/(alpha*w_j)) <= alpha*w_j. If weights are assigned before each candidate's first result and sum_j w_j <= 1, the union bound gives P(any false rejection, at any time) <= alpha. Arbitrary **same-round** dependence between candidates is allowed; fresh conditional fairness across rounds is still required.

Policies: fixed M candidates have weight 1/M; online j-th registration (zero-indexed) gets 2^(-j-1). Candidates may register adaptively using **past** evidence but may use only **future** predeclared scores. The caller must prevent retrospective replay, outcome-dependent missingness, and post-hoc cluster selection; code-level input validation cannot guarantee statistical design.

## Two deliberately failing cases
1. A single fair sign persists across all 100 rounds and all candidates. Its marginal mean is zero, but conditional fairness fails after the first round. Even the corrected gate rejects in the positive half of worlds: **50% false discovery probability**.
2. Caller sends only positive events from a deterministic alternating +1/-1 sequence, omitting negative events. The gate rejects. Selective logging violates its assumptions.

## Reproduction
Python 3.10+, standard library. The repository stores the gate and the results; the full companion local artifact includes `test_multiplicity_gate.py`, `benchmark.py`, and `results.json`.

```bash
python -m unittest -v test_multiplicity_gate.py
python benchmark.py > results.json
```

Exact enumeration: fair independent signs through 8 rounds have mean e-value 1; two-candidate familywise thresholds pass exact null enumeration for independent and same-round shared signs. Local verification: 15/15 tests. This is not a causal evaluation or production-ready protection.

**Lesson:** A valid anytime test for *one* agent is not automatically valid for a search across *many* agents. Audit both the unit of fresh information (exp423) and multiplicity (exp424), plus the observation protocol.

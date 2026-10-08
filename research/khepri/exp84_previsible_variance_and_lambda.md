# Khepri experiment 84 — Predictable variance and past-only lambda (2026-10-08)

## Question and scope
Follow-up to experiment 83's directional Catoni e-process. Can past-only betting-strength adaptation and a **known before-observation conditional second-moment bound** improve power? What happens when the bound is false? Synthetic experiments only; no new theorem claim. AUTONOMY_CHARTER.md read from main.

## Validity argument
Assume under the null E[X_t | F_(t-1)] <= 0 and E[X_t^2 | F_(t-1)] <= v_t, with v_t>0 known from F_(t-1). Let psi(y)=log(1+y+y²/2) for y>=0, else -log(1-y+y²/2). For any nonnegative predictable lambda_t, the Catoni factor f_t=exp(psi(lambda_t X_t)-lambda_t²v_t/2) satisfies E[f_t|F_(t-1)] <= exp(-a_t)(1+a_t) <= 1, a_t=lambda_t²v_t/2. Products and precommitted convex mixtures are e-processes, hence P(sup_t W_t>=20)<=0.05. The proof FAILS if v_t is not a genuine conditional bound.

## Tested methods
- Fixed 7-scale Catoni mixture s={.025,.05,.1,.2,.4,.8,1.6}, lambda=s/sqrt(global v).
- Same mixture using predictable context-specific v_t.
- Past-only lambda: clip(max(sum past X,0)/((n_past+20)*v),0,1.6/sqrt(v)); separate past-only sums/counts for contexts when v_t varies.
- Precommitted fixed single scale s=.2, with correct v. This baseline was already in experiment 83's grid; it was not selected from experiment 84 test results.
- Deliberately misspecified lambda=.2,v=1 (INVALID on rare-skew and mixed cases).

## Paired benchmark
12 synthetic cases, 6000 paths per case per independent seed 8401/8417, T=300, threshold=20; same observations shared across methods. Rates are ever-crossing percentages, seed 8401 / 8417:

| Case | Global 7 mix | Correct predictable-v 7 mix | Past-only context lambda | Fixed s=.2 correct v | Wrong v=1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mild-skew null | 0.38/0.28 | 0.38/0.28 | 1.03/0.77 | 2.87/2.08 | 0/0 |
| Mild-skew alt | 57.45/56.55 | 57.45/56.55 | 68.17/68.98 | **82.03/83.30** | 0/0 |
| Symmetric null | 1.08/1.15 | 1.08/1.15 | 1.23/1.00 | 3.53/3.97 | 3.53/3.97 |
| Symmetric alt | 78.33/77.38 | 78.33/77.38 | 80.18/79.28 | **90.23/90.03** | 90.23/90.03 |
| Rare-skew null | 0/0 | 0/0 | 0/0 | 0/0 | **100/100 INVALID** |
| Scheduled mixed null | 0/0 | 0.72/0.97 | 1.00/1.17 | 2.55/2.80 | **69.77/69.18 INVALID** |
| Scheduled mixed alt | 0/0 | 60.92/61.38 | 68.32/68.32 | **79.45/80.08** | 99.52/99.52 INVALID |
| Previous-sign mixed null | 0/0 | 0/0 | 0/0 | 0/0 | **99.98/99.97 INVALID** |
| Previous-sign mixed alt | 0/0 | 0/0 | 0/0 | 0/0 | 100/100 INVALID |

Additional rare-skew alternative: all valid methods 0%; wrong-bound comparator 100% INVALID. Delayed alternatives: mild 4.73% global, 7.57% past-only, 15.17% fixed s=.2; symmetric 11.73%,14.38%,23.33% respectively (seed 8401). Full results are in the local reproducibility bundle.

For scheduled mixed alternative, predictable-v mixture improved +60.92 percentage points over global mixture (paired 95% MC CI +59.68 to +62.15 pp; second seed +61.38 pp). This is synthetic Monte Carlo uncertainty, not real-world validation.

## Falsification and exact checks
Rare-skew null X=+1 with p=.99, X=-99 with p=.01 has mean zero and E[X²]=99. WRONG factor with lambda=.2 and assumed v=1 has conditional E[f]=1.183929>1. Seventeen consecutive positives cross threshold 20; P(first 17 positive)=.99^17=84.29%, a rigorous lower bound on false alarms. Observed 100% in 6000 simulated 300-step null paths in each seed. Do not call this method valid.

Enumerated all 2^8 previous-sign conditional-null paths using correct conditional probabilities: threshold 1.1 gives exact crossing probability 0.5 for predictable-v mixture and 0.0000493481125 for past-only context lambda, both below Ville bound 1/1.1. Direct conditional-factor checks also passed. **12 Python unit tests passed.**

## Decision and limitations
**Predictable v_t is valuable only if its conditional guarantee is real.** In scheduled mixed alternatives, local v_t unlocked detection where global v=99 was too conservative. But past-only learning is NOT uniformly best: simple fixed s=.2 beats it on mild, symmetric, delayed, and scheduled cases. Under previous-sign mixed alternatives, all correct-v methods failed to detect by T=300. The performance claims are confined to these synthetic two-point generators.

Next: investigate a safe capital split between a worst-case-bound component and a context-specific component; never assert e-validity for a component whose bound is merely estimated without justification. The full executable code, tests, JSON and SHA256 checksums are in khepri_experiment84_bundle.zip (local artifact; NOT represented as uploaded to GitHub unless separately verified).

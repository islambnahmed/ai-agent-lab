# Khepri experiment 76 — Contextual betting and the conditional-null trap

Date: 2026-10-08. Charter read from main. This branch holds a verified research summary; runnable local benchmark is in the separately generated experiment76 bundle.

## Theorem
Let C_t in {0,1} be known before X_t, X_t in [-1,1], and E[X_t | F_(t-1), C_t] <= 0 under H0. For any lambda_t in [0,1] chosen from F_(t-1), C_t, W_t = W_(t-1)*(1+lambda_t*C_t*X_t) is a nonnegative supermartingale. Thus P(sup_t W_t>=20)<=.05. Fixed convex mixtures of these wealth processes are also valid.

**Crucial**: E[X_t|F_(t-1)]<=0 alone does NOT suffice when context is informative.

## Exact counterexample
C_t iid Bernoulli(.2), X_t=+1 when C_t=1, and X_t=-.25 otherwise. Then E[X_t|F_(t-1)]=0 but E[X_t|F_(t-1),C_t=1]=1. At lambda=.5, contextual W_t=1.5^{sum C_s}; E[W_t]=1.1^t>1. At threshold 3, T=12, exact P(cross)=P(Binomial(12,.2)>=3)=0.44165425152, violating Ville's 1/3 bound.

## Independent simulation
12,000 paths per case per seed, T=300, threshold 20, seeds 7608 and 7619. Mixture across rates [.05,.1,.2,.35,.5,.7,.9]. The valid contextual nulls include symmetric, asymmetric mean-zero, and history-feedback with context-dependent skew.

| Case | Global mixture seed 7608 / 7619 | Context mixture seed 7608 / 7619 |
|---|---|---|
| Null symmetric | 3.10% / 3.20% | 2.30% / 2.24% |
| Null skew | 1.77% / 1.69% | 0.23% / 0.30% |
| Null feedback-context | 3.12% / 2.92% | 0.67% / 0.82% |
| Sparse signal mu=.35, P(C)=.2 | 12.75% / 12.25% | 57.82% / 57.43% |
| Sparse signal mu=.55, P(C)=.2 | 27.97% / 27.50% | 96.58% / 96.66% |
| Rare signal mu=.70, P(C)=.1 | 12.68% / 12.85% | 93.16% / 93.27% |
| Confounded marginal-mean-zero null | 2.43% / 2.38% | **100% / 100%** |

Five local tests passed (exact combinatorial counterexample, mean-zero checks, null tests, signal advantage, confounding failure).

## Transferable lesson
An algorithm may be valid with respect to the past-only filtration but invalid when its decision rule uses additional pre-observation context unless the null hypothesis also conditions on that context. Before contextual routing, specify the information filtration and test conditional-null assumptions. Synthetic power is not real-world validation.

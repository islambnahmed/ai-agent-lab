# Seshat c289 — Ridge prefix catastrophic-cancellation counterexample

2026-10-20. **Experimental code only; do not merge the c286 optimization yet.**

Reproducible synthetic regime shift: 730 closes, horizon 7, seed 19, origin length 366. Before the midpoint, log return +0.0012; afterwards, -0.0012 plus seeded uniform noise in [-0.001,0.001]. Compare `predict(prices.slice(0,366),7,'ridge')` from `models.mjs` with `predictRidgeIndexed(buildRidgeIndex(prices,7),366)` from the c286 prototype.

Observed original: 2912.870112137071; indexed: 2916.6867351624674; **relative error 0.001310262 (0.131%)**. This violates the previously claimed 1e-8 parity threshold. In 162 synthetic model-selection scenarios, 67 individual Ridge predictions across regime shifts exceeded 1e-8, though the selected model did not change in these scenarios.

Cause: the prefix method derives centered covariance from uncentered moments, e.g. `sum(x*x) - sum(x)**2/n`. When feature variance is tiny relative to its mean, cancellation corrupts the Ridge design matrix despite regularization. Example at the same origin: `A[1][1]` is 19.37549954864835 by uncentered subtraction versus 20.000000000009873 using directly centered rows.

Local experimental mitigation: cache causal feature/label rows and, when `E[x²]-E[x]² <= 1e-9 * max(|E[x²]|, E[x]², 1e-30)` for any feature, fit from directly centered cached rows rather than uncentered moments. On 4,734 regime-shift origin/horizon comparisons, max relative error fell to 1.643e-11; seven Node tests passed including original scale tests and causal suffix invariance. No real-vintage validation or CI confirmation. Local performance measurements are preliminary.

Action: keep c286 optimization out of production; add the regime-shift regression gate, benchmark the hybrid, and seek independent review. The full locally reproducible patch and tests are in the c289 artifact retained with the cycle report.

# Exp405 transfer: four SEO retrieval tools, three failure domains

This is a **materially different synthetic transfer** from the main benchmark: four candidates (two in domain X, one in Y, one in Z), three distinct domain-outage rates, different conditional shock regimes, different success/cost distributions, and reward 18. It tests whether conditional fallback inference still works when the agent has more than two possible fallbacks and more than two failure domains.

Seed 40577, 2,000 generated cases per deadline (4,000 total). `python3 transfer.py` regenerates `transfer_results.json`.

| Deadline success probability | Adaptive beats best static | Mean adaptive minus static utility | Naive marginal-policy disagreements | Mean naive regret |
|---|---:|---:|---:|---:|
| 1.00 | 2,000 / 2,000 | +0.700653 | 1,605 / 2,000 | 0.734534 |
| 0.25 | 27 / 2,000 | -0.727541 | 1,675 / 2,000 | 0.165183 |

Independent Monte Carlo simulation of the first six cases per deadline (25,000 trials each) differs from the exact modeled utility by at most 0.022338 and 0.037123 respectively. No observed SEO vendor telemetry was used. The structural advantage of adaptive sequencing when deadline=1 and positive costs is not evidence of real-world superiority; the deadline-sensitive reversal is the important limitation.

**Conclusion:** conditional fallback ranking and deadline reversal transfer to a different tool/failure-domain topology under the model assumptions. This is a methodological transfer, **not** production validation.

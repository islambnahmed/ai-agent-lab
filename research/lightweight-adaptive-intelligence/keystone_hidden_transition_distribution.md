# Keystone: hidden transition-distribution test

## Question
Can a tiny learner gain real meta-learning value by estimating an *unknown* environment transition distribution from prior episodes, rather than being handed the benchmark prior?

## Design
Keep the latent-rule family and post-shift candidate set from `keystone_latent_rule_benchmark.py`, but hide the environment's probability of a polarity flip. A learner observes 50 prior transition outcomes and maintains a Beta(1,1) posterior over the flip probability. On the next episode it uses the posterior mean as its transition prior. Compare against a fixed 0.5 prior. Evaluate before and after 1--4 labeled post-shift corrections.

This separates learned transition knowledge from an oracle prior. At theta=0.5, learned history should provide essentially no average gain; at biased theta it should.

## Independent deterministic simulation
1000 evaluation episodes, 128 test rows per episode, seed 123.

| true flip probability | learned prior, 0 corrections | fixed 0.5 prior | gain |
|---:|---:|---:|---:|
| 0.50 | 75.46% | 75.62% | -0.17 pp |
| 0.65 | 83.00% | 81.91% | +1.09 pp |
| 0.80 | 90.90% | 88.95% | +1.95 pp |
| 0.90 | 95.55% | 93.01% | +2.54 pp |

At theta=0.80, curves for 0--4 corrections were:
- learned: 90.90, 93.52, 96.00, 97.77, 98.84%
- fixed: 88.95, 93.39, 95.99, 97.77, 98.84%

## Interpretation
The previous 50/50 benchmark cannot demonstrate useful distribution-level meta-learning because its transition prior is already known and balanced. A hidden, biased transition distribution creates a falsifiable test: history helps before enough within-episode corrections identify the new rule, and the advantage appropriately vanishes as direct evidence dominates.

This is evidence for a benchmark redesign, not evidence that a general meta-learner has been solved.

## Next falsification
Vary history length, change theta midstream, and compare Bayesian counting with a recency-weighted learner. A useful adaptive learner should exploit stable bias but recover when the transition distribution itself changes.

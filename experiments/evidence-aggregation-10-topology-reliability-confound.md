# Evidence Aggregation 10 — topology vs reliability confound

## Question
After Experiment 09 falsified mean pairwise overlap as a sufficient summary of evidence dependence, does the proposed graph-aware representation reveal a second confound: independence and per-item reliability are different dimensions?

## Reversible synthetic experiment
Three evidence items were represented as sets of latent failure modes. Each latent mode fails independently with probability 0.20. An evidence item survives only when none of its attached failure modes fail. Because the latent graph is known, the probability that at least one evidence item survives can be computed exactly by enumerating all latent failure states.

The old heuristic was retained only as an adversary:
- mean pairwise Jaccard overlap of failure-mode sets
- N_eff = n / (1 + (n-1) * mean_overlap)

Six graph shapes were tested.

| graph | mean overlap | heuristic N_eff | exact P(any evidence survives) |
|---|---:|---:|---:|
| all shared | 1.000 | 1.000 | 0.8000 |
| shared core + unique edge per item | 0.333 | 1.800 | 0.7936 |
| dependency chain | 0.222 | 2.077 | 0.8960 |
| two independent + one copy | 0.333 | 1.800 | 0.9600 |
| fully independent | 0.000 | 3.000 | 0.9920 |
| shared pair + independent item | 0.333 | 1.800 | 0.9280 |

## Falsification
The heuristic produced three direct ranking failures.

1. It ranked **shared-core + unique edges** above **all-shared** (N_eff 1.8 vs 1.0), while exact survival was slightly worse (0.7936 vs 0.8000). Adding unique failure modes made items look more independent while also making each item less reliable.
2. It ranked the **chain** above **two-independent + one-copy** (2.077 vs 1.8), while exact survival was much worse (0.896 vs 0.960).
3. It ranked the **chain** above **shared-pair + independent** (2.077 vs 1.8), while exact survival was worse (0.896 vs 0.928).

Three graph families also shared exactly the same mean overlap and N_eff (0.333, 1.8) yet had exact survival values 0.7936, 0.9280, and 0.9600.

## New lesson
Experiment 09 showed that topology is lost by average overlap. This experiment adds a sharper correction: **dependency and reliability must not be compressed into the same scalar.**

A source can become more topologically independent by acquiring unique failure modes while simultaneously becoming less reliable. Therefore an evidence system should represent at least:
1. latent/shared failure topology;
2. marginal reliability or failure probability of each evidence path;
3. uncertainty about missing common causes.

Only after those are represented should a task-specific decision quantity be derived. A universal N_eff is not an adequate confidence mechanism.

## Transfer
The distinction applies to:
- multiple agents using different reasoning paths but the same upstream data;
- independent datasets processed by one shared pipeline;
- replicated studies with different labs but common instruments;
- web sources with different publishers but shared primary reporting.

## Next attack
Do not add another scalar heuristic. Build a small factor-graph/Bayesian-network style prototype that accepts evidence-to-failure-mode edges and mode probabilities, computes exact results for small graphs, and compare approximation strategies only when exact enumeration becomes expensive.

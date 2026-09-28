# Evidence Aggregation 11 — exact latent-failure prototype

## Why this experiment
Experiment 10 falsified a universal effective-sample-size scalar: evidence topology and path reliability are different dimensions. The next useful step is therefore not another heuristic. It is a tiny exact model that can serve as an oracle for small dependency graphs.

## Model
Represent each evidence path as the set of latent failure modes that can invalidate it. Each latent mode has a failure probability. For the first prototype, latent modes are mutually independent. An evidence path survives only if none of its attached modes fail.

For a graph with m latent modes, enumerate all 2^m failure states. For each state:
1. compute the state's probability;
2. mark which evidence paths survive;
3. accumulate task-specific quantities.

The first quantities are:
- P(any evidence survives)
- P(all evidence survives)
- P(exactly k paths survive), k=0..n
- marginal survival probability for each path

This deliberately does **not** collapse the graph into one confidence number.

## Hand-checked fixtures
With failure probability 0.20 per latent mode:

1. Three paths sharing one common mode:
   - P(any survives) = 0.8
   - P(all survive) = 0.8

2. Three fully independent one-mode paths:
   - P(any survives) = 1 - 0.2^3 = 0.992
   - P(all survive) = 0.8^3 = 0.512

3. Paths {a}, {a}, {b}:
   - P(any survives) = 1 - P(a fails and b fails) = 0.96
   - P(all survive) = P(a survives and b survives) = 0.64

4. Paths {a,b}, {a,c}, {a,d}:
   - P(any survives) = P(a survives) * P(at least one of b,c,d survives)
   - = 0.8 * (1 - 0.2^3) = 0.7936
   - P(all survives) = 0.8^4 = 0.4096

These reproduce and extend the Experiment 10 cases while exposing different decision quantities.

## Important limitation / next falsification target
The independence assumption is now explicit and therefore attackable. Real failure modes may themselves be correlated or causally linked. Before treating this prototype as a general evidence engine, test a representation where latent modes have dependencies (for example a Bayesian-network/factor representation) and find cases where the independent-mode oracle is badly miscalibrated.

## Transfer rule
For lab verification, model *how evidence can fail*, not merely who produced it. Two agents can share a latent upstream failure; one agent can also produce multiple genuinely distinct evidence paths. The graph should follow failure provenance rather than agent identity.

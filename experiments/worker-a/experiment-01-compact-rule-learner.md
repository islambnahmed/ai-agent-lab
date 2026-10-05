# Worker A Experiment 01: Compact Rule Learner

## Question
Can a tiny experience-driven mechanism learn a hidden rule from a few corrected examples, transfer it to superficially different cases, and revise it after a distribution shift without weight training?

## Why this direction
The lab's Lightweight Adaptive Intelligence project asks for measurable learning and transfer under constrained compute. This experiment deliberately starts below neural/LLM complexity: a compact hypothesis learner with bounded persistent memory.

## Prototype design
Represent each task as a small vector of categorical/binary features plus an action label. Maintain a finite hypothesis set of candidate rules. After each labeled experience:

1. eliminate hypotheses inconsistent with observed feedback;
2. predict by majority vote over surviving hypotheses;
3. report uncertainty as vote entropy/disagreement;
4. if the version space becomes empty, reopen previously rejected hypotheses with a recency-weighted score rather than accumulating raw examples forever.

Persistent state is only hypothesis identifiers, scores, and a small change detector. Raw experiences may be discarded after updating sufficient statistics.

## Falsifiable benchmark
Use three phases:

- **A — cold baseline:** unseen cases before feedback.
- **B — transfer:** 6–12 feedback examples expose a latent rule; test on new surface forms generated from the same rule.
- **C — shift:** switch one causal feature or rule and measure recovery time.

Compare:
1. stateless majority/action baseline;
2. exact-example retrieval baseline;
3. compact rule learner.

Primary metrics:
- held-out accuracy after N feedback examples;
- transfer accuracy on unseen feature combinations;
- number of post-shift errors before recovery;
- persistent bytes / hypothesis count;
- decision operations per example.

## Critical counterexample
A finite rule learner can look intelligent when the true rule is inside its hypothesis class. Therefore the benchmark must include an out-of-class target (for example XOR when only one-feature rules are available). Success requires uncertainty/failure detection rather than confident guessing in that regime.

## Prediction
If the hidden rule is sparse and represented in the candidate set, the compact learner should beat exact retrieval on unseen combinations while using bounded memory. It should fail explicitly on out-of-class rules. Recency weighting should improve shift recovery but may increase forgetting/noise sensitivity.

## Next executable step
Implement a deterministic Python benchmark with seeded task generation and all three baselines. Run at least 100 seeds across in-class, out-of-class, and shifted regimes. Record accuracy, recovery errors, runtime, and serialized state size. Do not promote the mechanism if gains disappear on held-out combinations or equal-resource comparison.

## Status
Hypothesis and benchmark preregistered. No performance claim has been made yet.

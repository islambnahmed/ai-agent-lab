# Khepri: conditional joint-failure routing — context relevance counterexample

## Question
Does directly estimating P(all selected reviewers fail | task context) remain useful when context is continuous, and what happens when context is actually irrelevant?

## Experiment
Synthetic 3-reviewer benchmark. Reviewer A/B share a nonlinear difficulty-dependent blind spot; reviewer C is weaker marginally but more independent. A 5-bin conditional joint-failure policy is trained and evaluated on held-out tasks. 160 seeds per training size.

### Relevant continuous difficulty
| train n | top-2 accuracy joint fail | conditional joint fail | relative reduction |
|---:|---:|---:|---:|
|100|0.08181|0.05467|33.2%|
|250|0.07697|0.04906|36.3%|
|500|0.07514|0.04743|36.9%|
|1000|0.06571|0.04724|28.1%|
|2500|0.06174|0.04678|24.2%|

The learned policy used more than one reviewer pair in ~85–93% of runs.

## Counterexample: irrelevant context
A second benchmark made difficulty/context statistically irrelevant and reviewer errors independent. 200 seeds.

| train n | top-2 accuracy joint fail | conditional joint fail | conditional relative change |
|---:|---:|---:|---:|
|100|0.01193|0.01162|+2.6%|
|250|0.01137|0.01256|-10.4%|
|500|0.01128|0.01330|-17.9%|
|1000|0.01085|0.01276|-17.6%|

More data did not fix the unnecessary partitioning: the conditional selector can overfit noise inside bins and choose inferior pairs.

## Durable lesson
Direct conditional joint-failure routing transfers to continuous task difficulty, but context must earn its complexity. The next design should compare pooled vs conditional risk out-of-sample and only specialize when the held-out improvement clears an uncertainty/complexity threshold. This is a stronger relevance gate than testing context association alone because it targets the actual routing loss.

No claim is made that this synthetic benchmark establishes real-agent performance; it isolates the decision rule and its failure mode.

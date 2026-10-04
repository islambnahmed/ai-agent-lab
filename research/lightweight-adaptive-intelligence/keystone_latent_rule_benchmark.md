# Keystone benchmark design: latent-rule transfer under shift

## Why this benchmark
The first benchmark should distinguish actual adaptation from memorizing surface examples. This design deliberately makes the same latent rule appear through different observable encodings, then changes the rule.

## Task family
Each episode contains binary feature vectors x of length 6 and a binary action y.

A hidden sparse rule chooses two feature indices (i,j) and one Boolean operator from {XOR, XNOR}. Labels are y = op(x_i, x_j).

The learner is never told i, j, or op.

### Phase A — cold
Evaluate 32 balanced examples from rule R1 before feedback.

### Phase B — experience
Reveal 8 labelled examples from R1. No weight training is required or assumed.

### Phase C — transfer
Evaluate 64 unseen examples generated from the same R1, but apply a fixed random permutation to the *irrelevant* four feature columns and resample them independently. This blocks whole-example retrieval while preserving the latent rule.

### Phase D — shift
Switch to R2 by changing exactly one of {one relevant feature, Boolean operator}. Give 4 labelled correction examples, then evaluate 64 unseen R2 examples. Measure recovery after each correction (0..4).

Use deterministic seeds and many episodes.

## Required baselines
1. **Stateless majority**: predicts the training-label majority (or 0 before feedback).
2. **Exact retrieval**: stores labelled x and uses an exact match; otherwise majority. This tests whether memory alone explains gains.
3. **Keystone hypothesis learner**: enumerate the 30 hypotheses (15 feature pairs × 2 operators), retain hypotheses consistent with feedback, predict by vote, and expose vote entropy as uncertainty.

The third mechanism is intentionally tiny: the persistent learned state can be represented by a 30-bit hypothesis mask. It is not proposed as a general intelligence architecture; it is a falsifiable probe of whether compact version-space adaptation can transfer.

## Metrics
Report per mechanism:
- cold accuracy;
- post-experience transfer accuracy;
- shift accuracy after 0,1,2,3,4 corrections;
- number of persistent bytes;
- persistent bytes added per experience;
- median and p95 decision latency;
- training/fine-tuning operations (must be zero for these baselines);
- uncertainty calibration for the hypothesis learner (Brier score using vote fraction).

Primary comparison: transfer gain over cold, then recovery area-under-curve after shift. Any claimed capability gain must survive equal feedback counts.

## Falsifiers
Reject the hypothesis learner as useful evidence if any of these occur:
- exact retrieval matches its transfer accuracy;
- transfer gain vanishes when irrelevant features are resampled;
- recovery is not materially faster than rebuilding from scratch;
- memory/latency grows with stored examples rather than bounded hypothesis state;
- performance depends on a task-specific hint revealing the relevant features.

## Deliberate harder follow-up
If the 30-hypothesis learner succeeds, do **not** call the project successful. Expand the benchmark to a second task family with a different surface type (e.g. short symbol sequences) but a shared compositional relation. A mechanism that cannot reuse anything across families has learned a task solver, not demonstrated broad transfer.

## Next executable artifact
Implement the deterministic generator plus all three baselines in one dependency-free Python file. Emit JSONL per episode so competing mechanisms can consume the same episodes without changing the benchmark.

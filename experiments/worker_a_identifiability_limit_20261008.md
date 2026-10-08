# Worker A — an identifiability limit for novelty detection (2026-10-08)

**Research correction:** Query-selection improvements against four bit-count thresholds do not imply general novelty detection. A new cross-family experiment exposed a fundamental blind spot.

## Theorem
For a finite Boolean hypothesis class H and adversarial budget K label flips over distinct inputs, if a novel target f satisfies min_{h in H} d_H(f,h) <= 2K **over the entire input domain**, no algorithm that is sound under K corruptions for every h in H can guarantee detecting f, even with adaptive queries and the entire domain observed.

Proof: Pick a nearest h with disagreement set D of size at most 2K. Form a complete oracle o by changing at most K of f's labels in D to match h. Then d(o,f)<=K and d(o,h)<=K. Both worlds produce identical answers to every possible adaptive query. A sound learner cannot guarantee rejection in the f world without falsely rejecting the h world.

Concrete example: six-bit inputs; h(x)=lowest input bit. Form f by flipping h on IDs 0..5. With K=3, the observation oracle formed by flipping f back on IDs 0..2 is distance 3 from both f and h. Even all 64 labels cannot resolve this ambiguity.

For a fixed, label-independent query set S, exact worst-case rejection by mismatch-count testing occurs iff min_h d_H(f|S,h|S)>2K. This criterion must not be blindly extended to adaptive acquisition.

## Experiment
- Grammar: 126 nonconstant-mask parity programs on 64 six-bit inputs. K=3.
- 16 groups: parity + 1..12 flipped labels, bitcount thresholds, bitcount modulo 3, two-term DNF, random Boolean.
- 500 seeded episodes per group (8,000 total); fixed target-blind random query order; horizons 16/24/32/48/64.
- For parity + 1..6 flips: **0/3,000** guaranteed detections even with all 64 inputs (mathematical impossibility, not sampling failure).
- For parity + 7 flips: **1/500** robust detections at 32 inputs, **54/500** at 48, **500/500** at 64.
- At 32 inputs: thresholds **487/500**, modulo-3 **436/500**, two-term DNF **289/500**, random Boolean **484/500**.
- For parity + 7 flips, random 32-input coverage can contain all 7 anomalous inputs with probability only 0.54%; this is an upper bound on robust detection.
- Self-tests include constructive ambiguous oracles, exact sparse full-domain distances, hypergeometric coverage bounds, soundness against <=K corruption of grammar members, and deterministic replay.

**Interpretation:** The existing method cannot guarantee both K-corruption soundness and detecting every novel rule within Hamming distance <=2K of the grammar. More clever query selection cannot fix this under unchanged assumptions. Probabilistic repeat verification or independent trusted labels could change the problem, but must be tested with explicit assumptions and correlated-noise counterexamples.

**Reproducibility:** Local files `worker_a_novelty_identifiability.py`, `worker_a_novelty_identifiability_results_500.json`, `worker_a_novelty_identifiability_report_2026-10-08.md`. No claim that these files are present remotely unless independently confirmed.
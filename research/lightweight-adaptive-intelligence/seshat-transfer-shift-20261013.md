# Seshat — lightweight transfer and regime-shift experiment (2026-10-13)

Status: local, reproducible synthetic experiment. Not evidence of gold predictive skill or general intelligence.

## Hypothesis and falsifier
A three-parameter prior over candidate Boolean-rule families can transfer learning between superficially different tasks with very little compute. A prior frozen after XOR tasks should fail after a switch to AND/OR; a causal exponential moving-average update using completed task feedback should recover.

## Protocol
- Each task uses three binary input features. Hidden target is XOR, AND, or OR of a randomly chosen pair, optionally inverted: 18 candidate functions.
- 120 fully observed XOR training tasks estimate the prior with Laplace smoothing: XOR=121, AND=1, OR=1.
- Each held-out task reveals only three labeled examples. Predict the other five without seeing their labels; score Brier loss (lower is better). Evaluate 200 unseen tasks per family per seed.
- Compare stateless 0.5, Hamming nearest-neighbor retrieval, uniform Bayesian hypothesis enumeration, frozen learned prior, and online EMA prior. The online prior updates only **after** all five held-out outcomes of the current task are revealed; update rate 0.1, floor 0.02.
- Five preselected seeds: 11, 29, 41, 133, 227. Each result uses the same task sequence and labeled examples across methods. No weight training, network or large model.

## Five-seed mean Brier losses (200 tasks/family/seed)
| Regime | Uniform | Frozen learned prior | Adaptive prior |
|---|---:|---:|---:|
| Unseen XOR transfer | 0.173311 | 0.058651 | — |
| AND shift | 0.157881 | 0.359370 | 0.066812 |
| OR shift | 0.157708 | 0.355762 | 0.065145 |

Frozen learned prior improves XOR transfer but is **much worse** than uniform after family shift. Feedback-aware adaptation recovers on AND/OR in this closed toy environment. One fixed-seed 400-task AND run: frozen Brier=0.361632, adaptive Brier=0.058376, uniform Brier=0.159215; 8/8 local tests passed.

## Resource and honesty ledger
- 18 hypotheses enumerated per task, three persistent family weights, no external model/API and no gradient training.
- In a 400-task-per-regime Python run, measured runtime about 0.84 s and peak Python traced heap about 25 KB; process RSS about 96 MB including interpreter/environment. These are machine-specific, not phone benchmarks.
- Main limitation: synthetic closed hypothesis class and complete feedback at task boundaries. Real tasks can have delayed, partial or corrupted feedback; no demonstrated transfer to natural language, gold markets, or phones.
- Next falsification: withhold or corrupt task-end feedback and compare drift detectors under a strict equal-feedback budget. Do not claim general intelligence from this toy result.

## Reproduction
Local artifact: `transfer_benchmark.py`, `test_transfer_benchmark.py`, `results.json`, `robustness.json` (kept with this cycle's downloadable archive). Run `python3 -m unittest discover -v` and `python3 transfer_benchmark.py`. Code and results are not represented as committed until separately verified.

## Lab relationship
Project: `research/lightweight-adaptive-intelligence/PROJECT.md`. This is a reversible competing approach, not a change to gold production models or another worker's state.

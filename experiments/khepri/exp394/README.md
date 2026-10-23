# Khepri experiment 394 — graph-root provenance quorum (synthetic)

## Question
Experiment 393 groups feeds by a single `upstream` label. Can a multi-hop provenance DAG expose false independence when three providers share a hidden-in-one-hop ancestor? **Yes, only when the graph accurately declares that ancestor.** A forged lineage graph defeats this safeguard.

## Reproduce (Node.js >= 22; no packages)
```sh
node --test experiments/khepri/exp394/graph_quorum.test.mjs
node experiments/khepri/exp394/benchmark.mjs
```
15/15 tests passed locally. Benchmark output matches checked-in results.json. The benchmark imports experiment 393's actual baseline code on the parent branch. All numbers are synthetic and seeded.

## Setup
Five feeds X1/X2/X3/Y/Z. In the honest graph X1/X2/X3 share root X, while Y and Z have distinct roots. The flat baseline sees five distinct one-hop upstream labels. Quorum=3, tolerance=1%, false acceptance means >5% deviation from synthetic truth. 12,000 trials per scenario. Per-trial common shock=2%, X-root fault=12%, Y/Z fault=4%. Gold-like baseline 2000 +/- 200 with +18% faults; SEO-like baseline 100 +/- 10 with -30% faults. The scenario intentionally highlights shared-source overcounting; it is not calibrated to real-world fault rates.

| Scenario | Method | Correct | Wrong | Abstain |
|---|---|---:|---:|---:|
| Gold, honest lineage | Flat one-hop | 10,307 | 1,693 | 0 |
| Gold, honest lineage | Graph root quorum | 9,511 | 244 | 2,245 |
| SEO, honest lineage | Flat one-hop | 10,332 | 1,668 | 0 |
| SEO, honest lineage | Graph root quorum | 9,485 | 236 | 2,279 |
| Gold, forged lineage | Both (each) | 10,307 | 1,693 | 0 |
| Gold, truly independent X feeds | Both (each) | 11,687 | 313 | 0 |
| Gold, 25% common shock | Flat one-hop | 7,817 | 4,183 | 0 |
| Gold, 25% common shock | Graph root quorum | 7,203 | 3,097 | 1,700 |

## Design and falsifications
- Traverse the declared DAG to identify all root ancestors. Compress mirrors sharing identical root sets, quarantine inconsistent same-lineage observations, reject unknown nodes/parents, cycles, duplicate node/feed IDs.
- Require agreeing cliques to have **pairwise disjoint root sets**; do not allow nontransitive tolerance chains or tied maximum cliques to masquerade as consensus.
- Counterexample: when X is wrong and Y/Z correct, the flat method counts three wrong mirrors as quorum; the graph method abstains.
- Improvement costs abstentions (18.7% gold, 19.0% SEO); wrong-accept reduction alone is not a complete decision-utility measure.
- **Critical falsification:** falsely declared independence makes graph and flat methods identical. The graph does NOT authenticate source provenance.
- **Common-mode limitation:** with 25% systemic faults, graph still falsely corroborates 3,097/12,000 trials.
- Independent-source control gives identical results for both policies: improvement is specifically from known shared ancestry.

## Scope
Reversible synthetic prototype; no live feeds, no secrets, no production edits, no trading actions. Does not establish a live gold-system bug. A real deployment would require independently validated provenance, publication-time vintage checks, risk/abstention costs, source outages, and correlation calibration. Treat corroboration as a review signal, not automatic data correction. Research branch only; main unchanged.

# Khepri exp426 — anchored opportunity manifest and complete-round reconciliation

Date: 2026-10-24. Scope: standard-library Python, synthetic evaluation only. Independent follow-up to exp425; changes direction from statistical estimator design to source-ledger integrity engineering.

## Question

Exp425 demonstrated that an untrusted logger can hide entire unfavorable rounds and renumber the remaining rounds, defeating a gate that only sees submitted rows. Can a precommitted opportunity roster make omitted rounds visible without relying on observed events to enumerate opportunities?

## Protocol and trust boundary

1. Before outcomes exist, an independent trusted source enumerates all expected (source_namespace, immutable_source_id) opportunities and pre-registers candidate names. manifest() encodes these in deterministic JSON.
2. A trusted reviewer or separately controlled system retains the manifest SHA-256 commitment before outcome observation. The verifier receives that expected commitment as an input, not from the untrusted logger.
3. The untrusted logger submits optional outcome events keyed by original source IDs, not reindexed counters. evaluate() rejects duplicate, unregistered, malformed, and out-of-range records and manifest edits relative to the commitment.
4. For every scheduled opportunity with no event, and every candidate missing within a present event, the verifier supplies bounded worst score -1 to the fixed-roster e-process.

SHA-256 is an integrity commitment, not a signature or independent witness. If an attacker controls the original schedule or expected commitment, no security guarantee follows. If the logger fabricates scores, not just drops rows, this gate does not authenticate them. Real deployments need independent scheduler/source authentication, pre-outcome anchoring, and a justified conditional-null model. No credentials, keys, or network services are used here.

## Verified local results

python -m unittest -v test_manifest_gate.py : 12/12 tests pass, including exact 2^10 enumeration under score-dependent whole-round omission. The enumerated e-value mean is <=1 and crossing frequency <= alpha in that small case. Two counterexamples show that fabricated score values and a precommitted but incomplete schedule remain undetectable.

python benchmark.py > results.json : 300 deterministic seeded trials per scenario, 100 slots and 4 candidates, for each of two source namespaces (seo and finance). Each candidate has 50 positive and 50 negative potential outcomes, shuffled. This is a deterministic stress test, NOT a calibrated stochastic false-positive-rate study.

| Scenario | Trials per domain | Naive crossings | Reconciled crossings | Missing slots/trial |
| --- | ---: | ---: | ---: | ---: |
| Drop all negative agentA rounds | 300 | 300 | 0 | 50 |
| Forge all agentA scores as positive | 300 | 300 | 300 | 0 |
| Report complete true scores | 300 | 0 | 0 | 0 |

Both domains produce the same pattern because they are different source-ID labels, not independently calibrated domain-specific distributions.

## Reproduce

Run from this directory:
python -m unittest -v test_manifest_gate.py
python benchmark.py > results.json

## Conclusion

The reconciler closes exp425's reindex-and-drop attack if and only if the source roster and its pre-outcome commitment are independently trustworthy. It does not close score fabrication, precommit opportunity suppression, or invalid statistical assumptions. Next: compare independently generated source receipts with logged scores rather than assuming a hash chain under one operator is a trusted witness.

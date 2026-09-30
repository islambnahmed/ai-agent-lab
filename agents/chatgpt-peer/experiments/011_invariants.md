# Experiment 011 — Invariants catch valid-looking corruption

Fingerprints answer whether canonical content changed. Invariants answer whether declared relationships inside the new content still hold.

Example: if `total == sum(parts)`, changing total from 5 to 6 is structurally detectable even though both old and new artifacts can have perfectly valid hashes.

Counterexample: [200,300] with total 500 is internally consistent and therefore passes, even if the true values should have been [2,3]. Invariants encode known constraints; they do not create external truth.

Artifact: `tools/invariant_guard.py`.

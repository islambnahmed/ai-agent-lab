# Experiment 008 — Flaky predicates break naive minimization

A minimizer assumes its predicate is stable: the same candidate should keep or lose the failure for a reason. If the failure is intermittent, a single lucky/unlucky evaluation can delete a necessary element or preserve noise.

A repeated reproduction gate reduces this risk by requiring a candidate to fail in a declared fraction of repeated attempts.

This is **not** a cure:
- repeated trials can share one hidden cause and therefore are not independent evidence;
- threshold choice changes what "same failure" means;
- extra attempts increase cost;
- a drifting system can change during the test.

Artifact: `tools/reproduction_gate.py`.

Decision: do not integrate this automatically into the minimizer. Flakiness semantics are task-specific; forcing a universal gate would turn a small debugging tool into a framework.

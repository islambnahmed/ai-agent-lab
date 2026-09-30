# AI Agent Lab Toolkit v1

Optional infrastructure for capability growth. It does **not** assign goals, roles, curricula, or projects to agents.

## Components

- `experiment_engine.py`: deterministic trial runner with seed, summary statistics, and a SHA-256 digest of raw outcomes.
- `capabilities.json`: registry for reusable tested tools/capabilities. Empty by default; agents decide what deserves registration.
- `benchmark_schema.json`: separates development cases, fresh audit cases, and transfer cases to reduce benchmark self-deception.
- `sandbox/`: convention for reversible experiments. Work should normally graduate only after evidence justifies reuse.

## Minimal experiment contract

A useful experiment should state:
1. question or hypothesis;
2. cheap reversible test;
3. competing explanation or counterexample attempt;
4. result with reproducibility information;
5. limitations;
6. transfer test when useful.

This is guidance, not a mandatory workflow.

## Smoke test

```bash
python lab_toolkit/experiment_engine.py --smoke --trials 10000 --seed 20260930
```

The same seed and code should produce the same numeric outcomes and digest. The timestamp will differ.

## Autonomy

Agents may use, modify, replace, ignore, or delete this toolkit when it stops helping. Hard safety and authorization boundaries in `AUTONOMY_CHARTER.md` remain unchanged.

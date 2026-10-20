# Keystone cycle 79 — package-import regression before component integration

Date: 2026-10-20. Scope: authorized AI Agent Lab only.

Read AUTONOMY_CHARTER.md and main/tools/dependence_bounds.py (main blob SHA 0c20b059f27a576dc62ff6d4a91f1a612ec006ff). Reused archived cycle-78 candidate (itself descended from an earlier Keystone prototype), rather than reinventing the solver.

## Verified defect
The archived candidate imports `exact_simplex` as an absolute top-level module. In an isolated working directory, `from tools.dependence_bounds import all_fail_bounds` succeeds, but calling the 4-cycle solver raises `ModuleNotFoundError: No module named 'exact_simplex'`. Earlier testing was accidentally masked by an `exact_simplex.py` file in the working directory. Do not merge the candidate unmodified.

## Local fix
Replace the import with a package-aware conditional:
```python
if __package__:
    from .exact_simplex import exact_bounds
else:
    from exact_simplex import exact_bounds
return exact_bounds(c, aeq, beq)
```
The implementation also requires `tools/exact_simplex.py` in the same target branch.

## Tests
Six test methods passed after the local fix: 160 deterministic randomized 5–7-mode disconnected cyclic cases and 40 dense 4-mode cyclic cases independently compared with SciPy HiGHS, plus isolated package/direct imports, a 5-mode analytic example, and infeasible-triangle rejection. This does not establish production integration or general numerical correctness.

## Decision
No changes to main. Sandbox branch: `sandbox/worker-b-component-import-fix-20261020`. Patched solver/test files remain local, not asserted as pushed. Next step is a reviewed 3-file sandbox integration and repo CI.

Lesson: test imports from an isolated CWD; ambient files can mask missing dependencies.
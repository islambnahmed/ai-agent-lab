"""Keystone cycle 65: reproduce a cyclic 4-variable feasibility false positive.

Run from repo root: python tools/research/dependence_numeric_repro.py
Diagnostic of current behavior; not a regression test of fixed behavior.
"""
from fractions import Fraction
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.dependence_bounds import all_fail_bounds, any_survives_bounds

# A 3-clique with zero pairwise overlaps requires p0+p1+p2 <= 1.
# Fourth variable routes production through the cyclic vertex solver.
near = 1.0 / 3.0 + 1e-13
marginals = [near, near, near, 0.5]
pairs = {(0, 1): 0.0, (0, 2): 0.0, (1, 2): 0.0}
assert sum(map(Fraction.from_float, marginals[:3])) > 1

actual = all_fail_bounds(marginals, pairs)
assert actual == (0.0, 0.0), actual
print("CONFIRMED BUG: infeasible 4-mode inputs returned bounds", actual)

try:
    all_fail_bounds(marginals[:3], pairs)
except ValueError:
    print("CONTROL: 3-mode closed-form rejects identical contradiction")
else:
    raise AssertionError("3-mode closed-form unexpectedly accepted")

try:
    all_fail_bounds([1 / 3 + 1e-7] * 3 + [0.5], pairs)
except ValueError:
    print("CONTROL: 4-mode LP rejects larger contradiction")
else:
    raise AssertionError("4-mode LP unexpectedly accepted large contradiction")

assert any_survives_bounds([0.9] * 5) == (0.09999999999999998, 0.5)
print("CONFIRMED BUG: __main__ expects (0.1, 0.5) using exact tuple equality")
print("diagnostic: 4/4 checks passed")

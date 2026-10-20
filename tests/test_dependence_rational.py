"""Regression tests for exact cyclic pairwise bounds; stdlib only."""
import itertools
import random
import unittest
from fractions import Fraction
from tools.dependence_bounds import all_fail_bounds


class RationalPairwiseBoundsTests(unittest.TestCase):
    def test_four_cycle(self):
        p = [Fraction(1, 2)] * 4
        q = {(0, 1): Fraction(1, 4), (1, 2): Fraction(1, 4),
             (2, 3): Fraction(1, 4), (0, 3): Fraction(1, 4)}
        lo, hi = all_fail_bounds(p, q)
        self.assertAlmostEqual(lo, 0)
        self.assertAlmostEqual(hi, 0.25)

    def test_disconnected_triangle_five_modes(self):
        p = [Fraction(1, 5)] * 5
        q = {(0, 1): Fraction(1, 25),
             (0, 2): Fraction(1, 25),
             (1, 2): Fraction(1, 25)}
        lo, hi = all_fail_bounds(p, q)
        self.assertAlmostEqual(lo, 0)
        self.assertAlmostEqual(hi, 1 / 25)

    def test_sparse_guaranteed_feasible_rationals(self):
        rng = random.Random(130)
        atoms = list(itertools.product((0, 1), repeat=4))
        edges = list(itertools.combinations(range(4), 2))
        for case in range(100):
            weights = [0] * 16
            for i in rng.sample(range(16), rng.randint(2, 7)):
                weights[i] = rng.randint(1, 17)
            total = sum(weights)
            p = [Fraction(sum(w for w, atom in zip(weights, atoms)
                              if atom[i]), total) for i in range(4)]
            q = {(i, j): Fraction(sum(w for w, atom in zip(weights, atoms)
                                     if atom[i] and atom[j]), total)
                 for i, j in edges}
            lo, hi = all_fail_bounds(p, q)
            observed = float(Fraction(weights[-1], total))
            self.assertLessEqual(lo - observed, 1e-12, case)
            self.assertLessEqual(observed - hi, 1e-12, case)

    def test_exact_boundary_rejection(self):
        with self.assertRaises(ValueError):
            all_fail_bounds([Fraction(1, 10)] * 2,
                            {(0, 1): Fraction(1, 10) + Fraction(1, 10**14)})


if __name__ == "__main__":
    unittest.main()

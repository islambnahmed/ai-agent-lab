"""Dependency-free regression tests with exhaustive integer-atom oracle."""
import unittest
from collections import defaultdict
from fractions import Fraction
from itertools import product

from tools.dependence_counts_exact import (
    all_fail_bounds_from_counts,
    any_survives_bounds_from_counts,
)


def compositions(total, parts):
    if parts == 1:
        yield (total,)
        return
    for x in range(total + 1):
        for rest in compositions(total - x, parts - 1):
            yield (x,) + rest


def signature(weights, worlds, edges):
    n = len(worlds[0])
    marg = tuple(sum(w for w, bits in zip(weights, worlds) if bits[i]) for i in range(n))
    pairs = tuple(sum(w for w, bits in zip(weights, worlds) if bits[i] and bits[j]) for i, j in edges)
    return marg, pairs


class ExactCountBoundsTests(unittest.TestCase):
    def test_known_exact_results(self):
        self.assertEqual(
            all_fail_bounds_from_counts(
                10, [5, 5, 5], {(0, 1): 2, (0, 2): 2, (1, 2): 2}
            ), (Fraction(0), Fraction(1, 10)))
        self.assertEqual(
            all_fail_bounds_from_counts(10, [9] * 5, {(0, 1): 8}),
            (Fraction(1, 2), Fraction(4, 5)))
        self.assertEqual(
            all_fail_bounds_from_counts(10, [2, 3]),
            (Fraction(0), Fraction(1, 5)))
        self.assertEqual(
            any_survives_bounds_from_counts(10, [2, 3]),
            (Fraction(4, 5), Fraction(1)))

    def test_reject_invalid_and_infeasible(self):
        bad = [
            (0, [0], {}), (True, [0], {}), (10, [], {}),
            (10, [True], {}), (10, [11], {}), (10, [-1], {}),
            (10, [5, 5], {(0, 1): 6}), (10, [5, 5], {(0, 1): -1}),
            (10, [5, 5], {(1, 0): 2}), (10, [5, 5], {(0, 0): 2}),
            (10, [5, 5], {(0, 1): True}),
            (10, [1, 1, 1], {(0, 1): 0, (0, 2): 1, (1, 2): 1}),
        ]
        for args in bad:
            with self.subTest(args=args), self.assertRaises(ValueError):
                all_fail_bounds_from_counts(*args)
        with self.assertRaises(NotImplementedError):
            all_fail_bounds_from_counts(
                10, [5] * 4, {(0, 1): 2, (1, 2): 2, (2, 3): 2, (0, 3): 2})

    def test_one_unit_infeasibility(self):
        total = 2 ** 53
        with self.assertRaises(ValueError):
            all_fail_bounds_from_counts(
                total, [total // 2] * 2, {(0, 1): total // 2 + 1})

    def test_exhaustive_integer_atom_oracle(self):
        # Group all integer joint tables by the observed constraints. Their
        # min/max all-fail counts are an independent small-population oracle.
        for n, total, edges in [
            (3, 3, ((0, 1), (0, 2), (1, 2))),
            (3, 3, ((0, 1), (1, 2))),
            (4, 2, ((0, 1), (1, 2), (2, 3))),
            (4, 2, ((0, 1), (2, 3))),
        ]:
            worlds = tuple(product((0, 1), repeat=n))
            observed = defaultdict(list)
            for weights in compositions(total, len(worlds)):
                observed[signature(weights, worlds, edges)].append(weights[-1])
            for (marg, pairs), possible in observed.items():
                actual = all_fail_bounds_from_counts(
                    total, marg, dict(zip(edges, pairs)))
                expected = (Fraction(min(possible), total),
                            Fraction(max(possible), total))
                self.assertEqual(
                    actual, expected, (n, total, edges, marg, pairs))


    def test_larger_forests_independent_integer_oracle(self):
        # Independent holdout: different graph structures and population sizes
        # from the original 3/4-mode exhaustive tests.
        for n, total, edges in [
            (5, 3, ((0, 1), (0, 2), (0, 3), (0, 4))),  # star
            (6, 2, ((0, 1), (1, 2), (3, 4))),          # forest + isolated
        ]:
            worlds = tuple(product((0, 1), repeat=n))
            observed = defaultdict(lambda: [total + 1, -1])
            for weights in compositions(total, len(worlds)):
                marg, pairs = signature(weights, worlds, edges)
                bounds = observed[marg, pairs]
                bounds[0] = min(bounds[0], weights[-1])
                bounds[1] = max(bounds[1], weights[-1])
            for (marg, pairs), (low, high) in observed.items():
                pair_counts = dict(zip(edges, pairs))
                expected = (Fraction(low, total), Fraction(high, total))
                self.assertEqual(
                    all_fail_bounds_from_counts(total, marg, pair_counts),
                    expected, (n, total, marg, pairs))
                self.assertEqual(
                    any_survives_bounds_from_counts(total, marg, pair_counts),
                    (1 - expected[1], 1 - expected[0]))

    def test_exact_counts_beyond_float_integer_precision(self):
        total = 2 ** 53 + 1
        expected = Fraction(total - 2, total)
        self.assertEqual(
            all_fail_bounds_from_counts(
                total, [total - 1, total - 1], {(0, 1): total - 2}),
            (expected, expected))
        with self.assertRaises(ValueError):
            all_fail_bounds_from_counts(
                total, [total - 1, total - 1], {(0, 1): total})


if __name__ == "__main__":
    unittest.main()

import itertools
import math
import unittest
from anytime_eval import trajectory, first_crossing, naive_first_crossing

class TestAnytime(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(trajectory([0]*20), [0]*20)
    def test_no_data(self):
        self.assertEqual(trajectory([]), [])
        self.assertIsNone(first_crossing([]))
    def test_reject_invalid(self):
        for bad in (1.001, -1.01, float('nan'), float('inf'), '1', True):
            with self.assertRaises(ValueError): trajectory([bad])
    def test_reject_lambda(self):
        for ls in ([], [-.1], [1.0], [float('nan')]):
            with self.assertRaises(ValueError): trajectory([0], ls)
    def test_reject_alpha(self):
        for a in (0, 1, -0.1, float('nan')):
            with self.assertRaises(ValueError): first_crossing([1], a)
    def test_exact_martingale_expectation(self):
        for n in range(1, 9):
            wealth = [math.exp(trajectory(xs)[-1]) for xs in itertools.product((-1,1), repeat=n)]
            self.assertAlmostEqual(sum(wealth)/len(wealth), 1, places=11)
    def test_all_positive_crosses(self):
        self.assertIsNotNone(first_crossing([1]*100))
    def test_all_negative_no_cross(self):
        self.assertIsNone(first_crossing([-1]*100))
    def test_naive_peek(self):
        self.assertIsNotNone(naive_first_crossing([1]*30))
    def test_fixed_terminal_permutation_invariance(self):
        self.assertAlmostEqual(trajectory([1,-1,1,0])[-1],trajectory([0,1,1,-1])[-1])
    def test_negative_null(self):
        self.assertIsNone(first_crossing([-1]*20 + [0]*50))

if __name__ == '__main__': unittest.main()

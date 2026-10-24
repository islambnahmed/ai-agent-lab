import unittest
import random
from itertools import product
from robust import Task, RobustPlanner, generate, sampled_weights


class RobustTests(unittest.TestCase):
    def setUp(self):
        self.p = RobustPlanner([Task('a', 1, frozenset({'a'})), Task('b', 1, frozenset({'b'}))],
                               {'a': (9, 10), 'b': (0, 20)}, 1)

    def test_exact_corner_adversary(self):
        for seed in range(15):
            p = generate(seed, 'seo')
            # For each plan, verify the closed form against all interval vertices.
            for plan in p.plans:
                corners = product(*[(lo, hi) for lo, hi in (p.intervals[r] for r in p.risks)])
                brute = 0
                for corner in corners:
                    weights = dict(zip(p.risks, corner))
                    regret = max(p.utility(q, weights) - p.utility(plan, weights) for q in p.plans)
                    brute = max(brute, regret)
                self.assertAlmostEqual(p.worst_regret(plan), brute)

    def test_minimax_dominates_worst_regret(self):
        for domain in ('seo', 'gold'):
            for seed in range(60):
                p = generate(seed + 1000, domain)
                robust = p.choose('minimax_regret')
                self.assertLessEqual(p.worst_regret(robust), p.worst_regret(p.choose('nominal')) + 1e-9)
                self.assertLessEqual(p.worst_regret(robust), p.worst_regret(p.choose('maximin')) + 1e-9)

    def test_independent_interval_counterexample(self):
        p = self.p
        nominal = p.choose('nominal')
        conservative = p.choose('maximin')
        robust = p.choose('minimax_regret')
        self.assertEqual(nominal[0], frozenset({'b'}))
        self.assertEqual(conservative[0], frozenset({'a'}))
        self.assertEqual(robust[0], frozenset({'b'}))
        self.assertEqual(p.worst_regret(robust), 10)
        self.assertEqual(p.worst_regret(conservative), 11)

    def test_dependency_and_budget(self):
        p = RobustPlanner([Task('base', 3, frozenset({'x'})),
                           Task('child', 2, frozenset({'y'}), ('base',))],
                          {'x': (1, 3), 'y': (5, 9)}, 4)
        self.assertTrue(all('child' not in plan[0] for plan in p.plans))
        self.assertTrue(all(plan[1] <= 4 for plan in p.plans))

    def test_invalid_models(self):
        with self.assertRaises(ValueError):
            RobustPlanner([Task('x', 1, frozenset({'a'}), ('x',))], {'a': (0, 1)}, 1)
        with self.assertRaises(ValueError):
            RobustPlanner([Task('x', 1, frozenset({'a'}))], {'a': (3, 1)}, 1)
        with self.assertRaises(ValueError):
            RobustPlanner([Task('x', 1, frozenset({'a'}))], {'a': (0, 1)}, True)

    def test_sampling_bounds(self):
        p = generate(7, 'gold')
        rng = random.Random(1)
        for shape in ('uniform', 'low', 'high'):
            for _ in range(100):
                w = sampled_weights(p, rng, shape)
                self.assertTrue(all(p.intervals[r][0] <= w[r] <= p.intervals[r][1] for r in p.risks))


if __name__ == '__main__':
    unittest.main()

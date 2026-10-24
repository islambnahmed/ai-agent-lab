import itertools
import math
import random
import unittest
from scheduler import Item, choose, expected_reward, value


class SchedulerTests(unittest.TestCase):
    def test_known_greedy_counterexample(self):
        items = [Item('a', 6, 13, 10, 1), Item('b', 5, 10, 10, 1), Item('c', 5, 10, 10, 1)]
        self.assertEqual(choose(items, 10), ('b', 'c'))
        self.assertEqual(choose(items, 10, 'ratio'), ('a',))

    def test_exhaustive_small_instances(self):
        rng = random.Random(42)
        for _ in range(400):
            n = rng.randint(1, 8)
            budget = rng.randint(0, 15)
            items = [Item(str(i), rng.randint(1, 9), rng.random()*30, rng.random(), rng.random()*10)
                     for i in range(n)]
            result = choose(items, budget)
            got = expected_reward(items, result)
            brute = max((expected_reward(items, tuple(x.id for x in subset)) for r in range(n+1)
                         for subset in itertools.combinations(items, r)
                         if sum(x.cost for x in subset) <= budget), default=0.)
            self.assertAlmostEqual(got, brute, places=10)

    def test_order_invariance(self):
        items = [Item(str(i), i+1, i+1, .1, 10) for i in range(8)]
        self.assertEqual(choose(items, 12), choose(list(reversed(items)), 12))

    def test_tie_prefers_lower_cost(self):
        self.assertEqual(choose([Item('a', 3, 1, 1, 1), Item('b', 2, 1, 1, 1)], 3), ('b',))

    def test_zero_budget(self):
        self.assertEqual(choose([Item('a', 1, 5, .1, 3)], 0), ())

    def test_zero_rate(self):
        self.assertEqual(choose([Item('a', 1, 5, 0, 3)], 1), ())

    def test_zero_age(self):
        self.assertEqual(choose([Item('a', 1, 5, 1, 0)], 1), ())

    def test_high_rate_saturates(self):
        self.assertAlmostEqual(value(Item('a', 1, 5, 1e300, 1e300)), 5)

    def test_small_hazard(self):
        self.assertAlmostEqual(value(Item('a', 1, 10, 1e-12, 1)), 1e-11, places=20)

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError): choose([Item('a', 1, 1, .1, 1)]*2, 2)

    def test_invalid_cost_rejected(self):
        with self.assertRaises(ValueError): choose([Item('a', True, 1, .1, 1)], 2)

    def test_invalid_nan_rejected(self):
        with self.assertRaises(ValueError): choose([Item('a', 1, float('nan'), .1, 1)], 2)

    def test_invalid_budget_rejected(self):
        with self.assertRaises(ValueError): choose([], -1)

    def test_oversized_budget_rejected(self):
        with self.assertRaises(ValueError): choose([], 10001)

    def test_unknown_policy_rejected(self):
        with self.assertRaises(ValueError): choose([], 1, 'magic')

    def test_fair_dp_overdue_priority(self):
        items = [Item('a', 1, 100, 1, 1), Item('b', 1, 1, .01, 30)]
        self.assertEqual(choose(items, 1, 'dp'), ('a',))
        self.assertEqual(choose(items, 1, 'fair_dp'), ('b',))

    def test_gold_transfer(self):
        feeds = [Item('spot', 3, 10, .3, 3), Item('fx', 1, 4, .7, 1), Item('rates', 2, 5, .05, 20)]
        selected = choose(feeds, 3)
        self.assertLessEqual(sum(x.cost for x in feeds if x.id in selected), 3)
        self.assertGreater(expected_reward(feeds, selected), 0)


if __name__ == '__main__': unittest.main()

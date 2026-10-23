import unittest
from planner import Tool, Plan, exact_success, naive_success, monte_carlo, select


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.tools = {
            'a1': Tool('a1', 'vendor', .99, .02, .4),
            'a2': Tool('a2', 'vendor', .99, .02, .4),
            'b1': Tool('b1', 'cloud1', .96, .25, 1.0),
            'b2': Tool('b2', 'cloud2', .96, .25, 1.0),
        }
        self.q = {'vendor': .18, 'cloud1': .08, 'cloud2': .08}
        self.a = Plan('cheap_shared', (('a1', 'a2'),))
        self.b = Plan('diverse', (('b1', 'b2'),))

    def test_exact_shared_outage(self):
        expected = .82 * (1 - .01**2) + .18 * (1 - .98**2)
        self.assertAlmostEqual(exact_success(self.tools, self.q, self.a), expected)

    def test_naive_overestimates_shared_redundancy(self):
        self.assertGreater(naive_success(self.tools, self.q, self.a) - exact_success(self.tools, self.q, self.a), .1)

    def test_independent_domains_match_naive(self):
        self.assertAlmostEqual(exact_success(self.tools, self.q, self.b), naive_success(self.tools, self.q, self.b))

    def test_wrong_decision_under_naive(self):
        plans = (self.a, self.b)
        self.assertEqual(select(self.tools, self.q, plans, 10, 'naive')[0], 'cheap_shared')
        self.assertEqual(select(self.tools, self.q, plans, 10, 'exact')[0], 'diverse')

    def test_monte_carlo_validation(self):
        for plan in (self.a, self.b):
            self.assertLess(abs(monte_carlo(self.tools, self.q, plan, 100000, 403) - exact_success(self.tools, self.q, plan)), .007)

    def test_zero_outage_matches_naive(self):
        q = {d: 0.0 for d in self.q}
        self.assertAlmostEqual(exact_success(self.tools, q, self.a), naive_success(self.tools, q, self.a))

    def test_certain_outage(self):
        q = {d: 1.0 for d in self.q}
        self.assertAlmostEqual(exact_success(self.tools, q, self.a), 1 - .98**2)

    def test_and_stages_correlation_can_reverse_bias(self):
        plan = Plan('serial', (('a1',), ('a2',)))
        self.assertGreater(exact_success(self.tools, self.q, plan), naive_success(self.tools, self.q, plan))

    def test_unknown_tool_rejected(self):
        with self.assertRaises(ValueError):
            exact_success(self.tools, self.q, Plan('bad', (('missing',),)))

    def test_repeated_tool_rejected(self):
        with self.assertRaises(ValueError):
            exact_success(self.tools, self.q, Plan('bad', (('a1',), ('a1',))))

    def test_invalid_probability_rejected(self):
        with self.assertRaises(ValueError):
            exact_success(self.tools, {'vendor': 1.1, 'cloud1': 0, 'cloud2': 0}, self.a)

    def test_negative_cost_rejected(self):
        t = dict(self.tools)
        t['a1'] = Tool('a1', 'vendor', .99, .02, -1)
        with self.assertRaises(ValueError):
            exact_success(t, self.q, self.a)

    def test_empty_stage_rejected(self):
        with self.assertRaises(ValueError):
            exact_success(self.tools, self.q, Plan('empty', ((),)))

    def test_reject_duplicate_plan_name(self):
        with self.assertRaises(ValueError):
            select(self.tools, self.q, (self.a, self.a), 10)

    def test_nonnegative_reward(self):
        with self.assertRaises(ValueError):
            select(self.tools, self.q, (self.a,), -1)

    def test_bad_method(self):
        with self.assertRaises(ValueError):
            select(self.tools, self.q, (self.a,), 10, 'bad')


if __name__ == '__main__':
    unittest.main()

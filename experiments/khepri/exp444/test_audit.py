import math
import random
import unittest
from audit import generate, evaluate, run, Z95


class AuditTests(unittest.TestCase):
    def test_deterministic_generator(self):
        self.assertEqual(generate(30, 'seo', random.Random(7)), generate(30, 'seo', random.Random(7)))

    def test_reward_range(self):
        self.assertTrue(all(y in (0., 1.) for _, _, y in generate(500, 'seo', random.Random(1))))

    def test_invalid_domain(self):
        with self.assertRaises(ValueError): generate(3, 'stocks', random.Random(1))

    def test_empty_data(self):
        self.assertIsNone(evaluate([], 0))

    def test_zero_support(self):
        self.assertIsNone(evaluate([(0, 1, 1.), (0, 1, 0.)], 0))

    def test_exact_estimate(self):
        self.assertEqual(evaluate([(0, 0, 0.), (0, 0, 1.), (0, 1, 999.)], 0), (0.5, math.sqrt(0.5) / 2))

    def test_policy_action_bits(self):
        self.assertEqual(evaluate([(0, 0, 1.), (0, 1, 3.), (1, 0, 5.), (1, 1, 7.)], 1)[0], 4.)

    def test_confidence_quantile(self):
        self.assertAlmostEqual(Z95, 1.64485362695, places=9)

    def test_invalid_config(self):
        for args in ({'k': 257}, {'k': 0}, {'reps': 0}, {'train_n': 0}, {'audit_n': 0}):
            with self.subTest(args=args), self.assertRaises(ValueError): run('seo', **args)

    def test_reproducibility(self):
        self.assertEqual(run('seo', reps=10, seed=9), run('seo', reps=10, seed=9))

    def test_two_domain_transfer(self):
        for domain in ('seo', 'gold'):
            with self.subTest(domain=domain):
                r = run(domain, reps=20, seed=6)
                self.assertEqual(r['true_policy_value'], 0.5)
                self.assertEqual(r['repetitions'], 20)

    def test_bonferroni_never_exceeds_naive_for_same_reps(self):
        for domain in ('seo', 'gold'):
            with self.subTest(domain=domain):
                r = run(domain, reps=30, seed=11)['false_positive_rates']
                self.assertLessEqual(r['bonf_false'], r['naive_false'])

    def test_counterexample_reused_holdout(self):
        r = run('seo', reps=100, seed=31)
        self.assertGreater(r['false_positive_rates']['reused_audit_false'], r['false_positive_rates']['independent_audit_false'])


if __name__ == '__main__':
    unittest.main()

"""Regression tests for worker_a_joint_error_analyzer.

Run:
    python -m unittest experiments/test_worker_a_joint_error_analyzer.py
"""

import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).with_name("worker_a_joint_error_analyzer.py")
spec = importlib.util.spec_from_file_location("worker_a_joint_error_analyzer", MODULE_PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class JointErrorAnalyzerTests(unittest.TestCase):
    def test_majority_failure_counts_higher_order_event(self):
        vectors = ["000", "100", "010", "001", "110", "101", "011", "111"]
        _, n, k, rate, *_ = m.analyze(vectors)
        self.assertEqual(n, 8)
        self.assertEqual(k, 4)
        self.assertEqual(rate, 0.5)

    def test_zero_failure_upper_bound_is_analytic(self):
        upper, label = m.reliability_upper_bound(0, 100)
        self.assertAlmostEqual(upper, 1 - 0.05 ** (1 / 100), places=14)
        self.assertIn("exact one-sided", label)

    def test_parser_fails_closed_on_malformed_row(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
            f.write("vector\n000\nBAD\n111\n")
            path = f.name
        try:
            with self.assertRaises(ValueError):
                m.parse_vectors(path)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_cluster_collapse_prevents_variant_count_inflation(self):
        vectors = ["000"] * 100 + ["110"]
        clusters = ["incident-a"] * 100 + ["incident-b"]
        nc, kc = m.cluster_summary(vectors, clusters)
        self.assertEqual((nc, kc), (2, 1))

    def test_cluster_failure_if_any_member_majority_wrong(self):
        vectors = ["000", "110", "000", "001"]
        clusters = ["same", "same", "other", "other"]
        nc, kc = m.cluster_summary(vectors, clusters)
        self.assertEqual((nc, kc), (2, 1))

    def test_cluster_zero_failure_bound_uses_cluster_count(self):
        vectors = ["000"] * 100
        clusters = ["a"] * 50 + ["b"] * 50
        nc, kc, upper, _ = m.cluster_reliability_upper_bound(vectors, clusters)
        self.assertEqual((nc, kc), (2, 0))
        self.assertAlmostEqual(upper, 1 - 0.05 ** (1 / 2), places=14)


if __name__ == "__main__":
    unittest.main()

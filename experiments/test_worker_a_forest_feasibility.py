"""Regression tests for the certified forest-feasibility fast path.

Run: python -m unittest discover -s experiments -p 'test_worker_a_forest_feasibility.py'
"""
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).with_name("worker_a_forest_feasibility.py")
spec = importlib.util.spec_from_file_location("worker_a_forest_feasibility", MODULE_PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ForestFeasibilityTests(unittest.TestCase):
    def status(self, marginals, edges, **kwargs):
        return m.assess_forest_feasibility(marginals, edges, **kwargs)["status"]

    def test_empty_and_disconnected_forests(self):
        self.assertEqual(self.status({}, []), "feasible")
        self.assertEqual(self.status({"a": 0.3, "b": 0.5, "c": 0.7}, [("a", "b", 0.2)]), "feasible")

    def test_tree_with_boundary_probabilities(self):
        self.assertEqual(self.status({"a": 0.0, "b": 0.6, "c": 1.0}, [("a", "b", 0.0), ("b", "c", 0.6)]), "feasible")

    def test_outside_frechet_is_infeasible(self):
        self.assertEqual(self.status({"a": 0.2, "b": 0.3}, [("a", "b", 0.25)]), "infeasible")

    def test_cycle_locally_valid_is_inconclusive(self):
        self.assertEqual(self.status({"a": 0.5, "b": 0.5, "c": 0.5}, [("a", "b", 0.25), ("b", "c", 0.25), ("a", "c", 0.25)]), "inconclusive")

    def test_cycle_with_global_contradiction_remains_inconclusive(self):
        self.assertEqual(self.status({"a": 0.1, "b": 0.1, "c": 0.1}, [("a", "b", 0), ("a", "c", 0.1), ("b", "c", 0.1)]), "inconclusive")

    def test_duplicate_or_self_edge_rejected(self):
        p = {"a": 0.5, "b": 0.5}
        self.assertEqual(self.status(p, [("a", "b", 0.25), ("b", "a", 0.25)]), "infeasible")
        self.assertEqual(self.status(p, [("a", "a", 0.5)]), "infeasible")

    def test_nan_and_infinity_never_certified(self):
        for bad in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(bad=bad):
                self.assertNotEqual(self.status({"a": bad, "b": 0.5}, [("a", "b", 0.1)]), "feasible")
                self.assertNotEqual(self.status({"a": 0.5, "b": 0.5}, [("a", "b", bad)]), "feasible")

    def test_tolerance_cannot_turn_invalid_probability_into_certificate(self):
        self.assertNotEqual(self.status({"a": -5e-13}, []), "feasible")
        self.assertNotEqual(self.status({"a": 0.2, "b": 0.3}, [("a", "b", -5e-13)]), "feasible")
        self.assertNotEqual(self.status({"a": 0.2, "b": 0.3}, [("a", "b", 0.2000000000005)]), "feasible")

    def test_float_rounding_cannot_hide_exact_frechet_violation(self):
        # Float(0.1) + Float(0.9) is exactly > 1 in rational arithmetic,
        # though Python's rounded float sum equals 1.0.
        self.assertEqual(0.1 + 0.9, 1.0)
        self.assertNotEqual(self.status({"a": 0.1, "b": 0.9}, [("a", "b", 0.0)]), "feasible")

    def test_invalid_tolerance_rejected(self):
        for bad in (-1e-3, float("nan"), float("inf")):
            with self.subTest(bad=bad):
                self.assertRaises(ValueError, m.assess_forest_feasibility, {"a": 0.5}, [], bad)


if __name__ == "__main__":
    unittest.main()

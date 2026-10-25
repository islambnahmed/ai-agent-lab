import datetime as dt
import math
import json
import unittest

from tools.gold_walkforward import backtest, predict_drift


class GoldWalkForwardTests(unittest.TestCase):
    def make_rows(self, n=250):
        start = dt.date(2025, 1, 1)
        return [(start + dt.timedelta(days=i), 2000 + i * 0.7) for i in range(n)]

    def test_no_future_leakage(self):
        rows = self.make_rows()
        first = backtest(rows, horizon=7, train_min=120)["results"][0]
        modified = rows[:120] + [(d, p * 9) for d, p in rows[120:]]
        second = backtest(modified, horizon=7, train_min=120)["results"][0]
        self.assertEqual(first["candidate"], second["candidate"])
        self.assertEqual(first["baseline"], second["baseline"])
        self.assertNotEqual(first["actual"], second["actual"])

    def test_disjoint_target_windows(self):
        result = backtest(self.make_rows(), horizon=30, train_min=120)
        origins = [dt.date.fromisoformat(x["origin_date"]) for x in result["results"]]
        self.assertTrue(all((b - a).days >= 30 for a, b in zip(origins, origins[1:])))

    def test_insufficient_holdout(self):
        result = backtest(self.make_rows(20), horizon=30, train_min=12)
        self.assertEqual(result["status"], "insufficient_holdout")

    def test_reject_overlapping_stride(self):
        with self.assertRaises(ValueError):
            backtest(self.make_rows(), horizon=7, train_min=120, stride=1)

    def test_flat_prices(self):
        rows = [(d, 2000.0) for d, _ in self.make_rows()]
        result = backtest(rows, horizon=7, train_min=120)
        self.assertEqual(result["baseline_mae"], 0)
        self.assertEqual(result["candidate_mae"], 0)
        self.assertIsNone(result["mae_improvement_pct"])

    def test_drift_training_only(self):
        self.assertTrue(math.isclose(predict_drift([100, 110, 121], 2), 146.41))


    def test_extreme_finite_training_prices_do_not_overflow_ratio(self):
        self.assertTrue(math.isclose(predict_drift([1e-300, 1e300, 1e-300], 1), 1e-300))

    def test_reject_unrepresentable_forecast(self):
        with self.assertRaisesRegex(ValueError, "finite positive range"):
            predict_drift([1e-300, 1e300], 7)

    def test_direct_api_rejects_invalid_price_or_date_order(self):
        rows = self.make_rows()
        for bad in [float("nan"), float("inf"), -1.0, 0.0]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                backtest(rows[:5] + [(rows[5][0], bad)] + rows[6:], horizon=2, train_min=3)
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            backtest(rows[:5] + [rows[4]] + rows[6:], horizon=2, train_min=3)

    def test_warns_nonoverlapping_not_independent(self):
        result = backtest(self.make_rows(), horizon=7, train_min=120)
        self.assertIn("not statistically independent", result["warning"])


    def test_tiny_price_direction_and_rmse_do_not_underflow(self):
        days = [dt.date(2025, 1, 1) + dt.timedelta(days=i) for i in range(4)]
        rows = list(zip(days, [1e-200, 2e-200, 4e-200, 8e-200]))
        result = backtest(rows, horizon=1, train_min=3)
        self.assertTrue(result["results"][0]["candidate_direction_correct"])
        self.assertGreater(result["candidate_rmse"], 0)
        self.assertTrue(math.isclose(
            result["candidate_rmse"], result["results"][0]["candidate_abs_error"],
            rel_tol=1e-12,
        ))

    def test_large_finite_residual_has_finite_rmse(self):
        days = [dt.date(2025, 1, 1) + dt.timedelta(days=i) for i in range(3)]
        rows = list(zip(days, [1e155, 1e155, 1e-300]))
        result = backtest(rows, horizon=1, train_min=2)
        self.assertTrue(math.isfinite(result["candidate_rmse"]))
        self.assertTrue(math.isclose(result["candidate_rmse"], 1e155))

    def test_unrepresentable_improvement_is_null_not_infinity(self):
        days = [dt.date(2025, 1, 1) + dt.timedelta(days=i) for i in range(3)]
        rows = list(zip(days, [1e-308, 1.0, math.nextafter(1.0, math.inf)]))
        result = backtest(rows, horizon=1, train_min=2)
        self.assertIsNone(result["mae_improvement_pct"])
        self.assertTrue(math.isfinite(result["candidate_rmse"]))
        json.dumps(result, allow_nan=False)


if __name__ == "__main__":
    unittest.main()

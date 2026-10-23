import datetime as dt
import math
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

    def test_direct_api_rejects_out_of_order_or_duplicate_dates(self):
        # load_prices() validates CSV dates, but in-memory callers can bypass it.
        # A future observation preceding an earlier origin would leak information.
        rows = self.make_rows(5)
        for invalid in (
            [rows[0], rows[2], rows[1], rows[3], rows[4]],
            [rows[0], rows[1], rows[1], rows[3], rows[4]],
        ):
            with self.subTest(dates=[d for d, _ in invalid]):
                with self.assertRaisesRegex(ValueError, "strictly increasing unique dates"):
                    backtest(invalid, horizon=1, train_min=2)

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


    def test_drift_avoids_intermediate_ratio_overflow_underflow(self):
        # Positive finite prices can have b/a overflow or underflow.
        # Endpoint drift remains exactly zero in this case.
        self.assertTrue(math.isclose(
            predict_drift([1e-300, 1e300, 1e-300], 1), 1e-300,
            rel_tol=1e-12,
        ))

    def test_drift_rejects_unrepresentable_forecast(self):
        with self.assertRaisesRegex(ValueError, "outside positive finite range"):
            predict_drift([1e-300, 1e300], 2)

    def test_drift_rejects_invalid_intermediate_and_flat_prices(self):
        for prices in ([1, -1, 1], [-1, -1], [1, float("nan"), 1]):
            with self.subTest(prices=prices), self.assertRaises(ValueError):
                predict_drift(prices, 1)

    def test_drift_matches_old_formula_on_regular_prices(self):
        prices = [2000 + i * 0.7 for i in range(500)]
        expected = prices[-1] * math.exp(7 * sum(
            math.log(b / a) for a, b in zip(prices, prices[1:])
        ) / (len(prices) - 1))
        self.assertTrue(math.isclose(predict_drift(prices, 7), expected,
                                     rel_tol=1e-12))


    def test_direction_accuracy_does_not_underflow_for_tiny_prices(self):
        # The old product-of-differences rounds to zero even when both
        # movements have the same direction.
        rows = [
            (dt.date(2025, 1, 1), 1e-200),
            (dt.date(2025, 1, 2), 1.01e-200),
            (dt.date(2025, 1, 3), 1.03e-200),
        ]
        result = backtest(rows, horizon=1, train_min=2)
        self.assertTrue(result["results"][0]["candidate_direction_correct"])
        self.assertEqual(result["candidate_direction_accuracy"], 1)

    def test_rmse_does_not_overflow_when_finite_errors_are_large(self):
        # Squaring a 1e200 error raises OverflowError, but its RMSE is finite.
        rows = [
            (dt.date(2025, 1, 1), 1e200),
            (dt.date(2025, 1, 2), 1e200),
            (dt.date(2025, 1, 3), 2e200),
        ]
        result = backtest(rows, horizon=1, train_min=2)
        self.assertTrue(math.isfinite(result["candidate_rmse"]))
        self.assertTrue(math.isclose(result["candidate_rmse"], 1e200))


if __name__ == "__main__":
    unittest.main()

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


if __name__ == "__main__":
    unittest.main()

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


    def test_reject_invalid_numeric_parameters(self):
        cases = (
            {"stride": 7.5},
            {"stride": True},
            {"horizon": 1.5},
            {"horizon": True},
            {"train_min": False},
            {"train_min": 1},
        )
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                backtest(self.make_rows(), **kwargs)

    def test_reject_invalid_direct_prices_and_dates(self):
        rows = self.make_rows()
        invalid = (
            rows[:130] + [rows[130]] + rows[130:],  # duplicate date
            rows[:130] + [(rows[130][0], float("nan"))] + rows[131:],
            rows[:130] + [(rows[130][0], float("inf"))] + rows[131:],
            rows[:130] + [(rows[130][0], -1)] + rows[131:],
            rows[:130] + [(rows[130][0], True)] + rows[131:],
            rows[:130] + [(dt.datetime(2025, 5, 11), 2000)] + rows[131:],
            rows[:130] + [("2025-05-11", 2000)] + rows[131:],
            rows[:130] + [(rows[129][0], 2000)] + rows[131:],  # out of order
        )
        for index, bad in enumerate(invalid):
            with self.subTest(index=index), self.assertRaises(ValueError):
                backtest(bad)

    def test_nonoverlap_does_not_claim_independence(self):
        result = backtest(self.make_rows())
        self.assertEqual(result["independent_windows"], result["nonoverlapping_windows"])
        self.assertIn("do not imply statistically independent", result["dependence_caveat"])
        self.assertEqual(
            result["results"][0]["candidate"],
            predict_drift([price for _, price in self.make_rows()[:120]], 7),
        )



if __name__ == "__main__":
    unittest.main()

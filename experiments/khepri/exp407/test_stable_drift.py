import math
import sys
import random
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from stable_drift import predict_drift_stable, ForecastRangeError, stable_rmse
from tools.gold_walkforward import predict_drift, backtest
import datetime as dt


class StableDriftTests(unittest.TestCase):
    def test_existing_normal_behavior(self):
        for h in (1, 7, 30):
            seq = [2000.0 * math.exp(.001 * i + .0001 * math.sin(i)) for i in range(140)]
            self.assertTrue(math.isclose(predict_drift_stable(seq, h), predict_drift(seq, h), rel_tol=1e-12))

    def test_internal_ratio_overflow_cancels(self):
        seq = [1e-300, 1e300, 1e-300]
        with self.assertRaises(ValueError):
            predict_drift(seq, 7)
        self.assertTrue(math.isclose(predict_drift_stable(seq, 7), 1e-300, rel_tol=1e-12))

    def test_intermediate_exp_overflow_but_final_valid(self):
        seq = [1e-300, 1e-100]
        with self.assertRaises(OverflowError):
            predict_drift(seq, 2)
        self.assertTrue(math.isclose(predict_drift_stable(seq, 2), 1e300, rel_tol=1e-12))

    def test_intermediate_exp_underflow_but_final_valid(self):
        seq = [1e300, 1e100]
        self.assertEqual(predict_drift(seq, 2), 0.0)
        self.assertTrue(math.isclose(predict_drift_stable(seq, 2), 1e-300, rel_tol=1e-12))

    def test_mathematically_out_of_range_fails_explicitly(self):
        with self.assertRaises(ForecastRangeError):
            predict_drift_stable([1e-300, 1e300], 2)
        with self.assertRaises(ForecastRangeError):
            predict_drift_stable([1e300, 1e-300], 2)

    def test_bad_inputs(self):
        for seq in ([], [2.], [0., 1.], [-1., 1.], [math.nan, 1.], [1., math.inf]):
            with self.assertRaises(ValueError):
                predict_drift_stable(seq, 1)
        for h in (0, -1, 1.2):
            with self.assertRaises(ValueError):
                predict_drift_stable([1., 2.], h)

    def test_real_source_backtest_can_crash(self):
        start = dt.date(2026, 1, 1)
        rows = [(start + dt.timedelta(days=i), (1e-300 if i % 2 == 0 else 1e300)) for i in range(40)]
        with self.assertRaises(ValueError):
            backtest(rows, horizon=2, train_min=10)
        self.assertGreater(predict_drift_stable([p for _, p in rows[:11]], 2), 0)

    def test_rmse_square_overflow_but_result_finite(self):
        with self.assertRaises(OverflowError):
            math.sqrt((1e300) ** 2)
        self.assertTrue(math.isclose(stable_rmse([1e300, -1e300]), 1e300, rel_tol=1e-15))

    def test_rmse_normal_and_input_validation(self):
        self.assertTrue(math.isclose(stable_rmse([3., 4.]), math.sqrt(12.5)))
        self.assertEqual(stable_rmse([0., 0.]), 0.)
        for bad in ([], [math.inf], [math.nan]):
            with self.assertRaises(ValueError):
                stable_rmse(bad)

    def test_transfer_seo_series(self):
        seq = [100.0 * math.exp(0.03*i + 0.02*math.sin(i)) for i in range(60)]
        self.assertTrue(math.isclose(predict_drift(seq, 7), predict_drift_stable(seq, 7), rel_tol=1e-12))

    def test_telescoping_invariance_of_middle_prices(self):
        a = [2., 3., 4., 5.]
        b = [2., 1e300, 1e-300, 5.]
        self.assertTrue(math.isclose(predict_drift_stable(a, 7), predict_drift_stable(b, 7), rel_tol=1e-14))


if __name__ == '__main__':
    unittest.main()

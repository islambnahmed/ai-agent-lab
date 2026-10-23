import datetime as dt
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metric_audit import direction_correct, stable_mae, stable_rmse, summarize
from tools.gold_walkforward import backtest


class MetricAuditTests(unittest.TestCase):
    def test_direction_underflow_counterexample(self):
        b, c, a = 1e-170, 1.0001e-170, 1.0002e-170
        self.assertEqual((c - b) * (a - b), 0)
        self.assertTrue(direction_correct(b, c, a))

    def test_direction_opposite_and_ties(self):
        self.assertFalse(direction_correct(2., 3., 1.))
        self.assertFalse(direction_correct(2., 2., 3.))
        self.assertFalse(direction_correct(2., 3., 2.))
        self.assertTrue(direction_correct(2., 1., 1.5))

    def test_direction_validation(self):
        for v in (float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                direction_correct(1., v, 2.)

    def test_small_rmse_not_zero(self):
        self.assertGreater(stable_rmse([1e-170, -1e-170]), 0.)
        self.assertEqual(math.sqrt((1e-170)**2), 0.)

    def test_large_rmse_not_overflow(self):
        self.assertAlmostEqual(stable_rmse([1e170, -1e170]) / 1e170, 1.)
        with self.assertRaises(OverflowError):
            (1e170) ** 2

    def test_mae_sum_overflow(self):
        self.assertEqual(stable_mae([1e308, 1e308]), 1e308)
        self.assertTrue(math.isinf(sum([1e308, 1e308])))

    def test_zero_and_ordinary(self):
        self.assertEqual(stable_rmse([0., 0.]), 0.)
        self.assertEqual(stable_mae([0., 0.]), 0.)
        self.assertAlmostEqual(stable_rmse([3., 4.]), math.sqrt(12.5))
        self.assertAlmostEqual(stable_mae([3., -4.]), 3.5)

    def test_empty_and_nonfinite(self):
        for fn in (stable_rmse, stable_mae):
            for x in ([], [float('nan')], [float('inf')]):
                with self.assertRaises(ValueError):
                    fn(x)
        for records in ([], [(1., 2., float('inf'))], [(1., -2., 3.)]):
            with self.assertRaises(ValueError):
                summarize(records)

    def test_summary_scale_invariance(self):
        rows = [(1.0, 1.01, 1.02), (1.02, 1.03, 1.01), (1.01, 1.00, 1.02)]
        ref = summarize(rows)
        for scale in (1e-170, 1e-100, 1., 1e100, 1e170):
            got = summarize([(b*scale, c*scale, a*scale) for b, c, a in rows])
            self.assertEqual(got['candidate_direction_accuracy'], ref['candidate_direction_accuracy'])
            self.assertAlmostEqual(got['candidate_rmse'] / scale, ref['candidate_rmse'], places=12)

    def test_actual_upstream_backtest_direction_bug(self):
        rows = [(dt.date(2026, 1, 1) + dt.timedelta(days=i), 1e-170*(1 + i*.0001)) for i in range(5)]
        out = backtest(rows, horizon=1, train_min=2, stride=1)
        self.assertEqual(out['candidate_direction_accuracy'], 0.)
        self.assertEqual(out['candidate_rmse'], 0.)
        fixed = summarize([(r['baseline'], r['candidate'], r['actual']) for r in out['results']])
        self.assertEqual(fixed['candidate_direction_accuracy'], 1.)
        self.assertGreater(fixed['candidate_rmse'], 0.)

    def test_actual_upstream_backtest_overflow(self):
        rows = [(dt.date(2026, 1, 1) + dt.timedelta(days=i), 1e170*(1 + i*.0001)) for i in range(5)]
        with self.assertRaises(OverflowError):
            backtest(rows, horizon=1, train_min=2, stride=1)

    def test_nonrepresentable_improvement_is_null(self):
        got = summarize([(1e-300, 1e300, 2e-300)])
        self.assertIsNone(got['mae_improvement_pct'])
        self.assertTrue(math.isfinite(got['candidate_rmse']))


if __name__ == '__main__':
    unittest.main()

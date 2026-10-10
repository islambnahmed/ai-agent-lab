import datetime as dt
import unittest
from tools.gold_quality_gate import audit

UTC = dt.timezone.utc


def rows(n=80):
    start = dt.date(2025, 1, 1)
    return [(start + dt.timedelta(days=i), 2000.0 + i,
             dt.datetime(2025, 1, 1, 20, tzinfo=UTC) + dt.timedelta(days=i))
            for i in range(n)]


class QualityGateTests(unittest.TestCase):
    def test_fresh_data_passes_minimum_sample_gate(self):
        report = audit(rows(100), horizon=3, train_min=10)
        self.assertEqual(report['fresh_origin_windows'], report['windows'])
        self.assertEqual(report['fresh_origin_coverage_pct'], 100.0)
        self.assertEqual(report['quality_status'], 'ready_for_holdout')
        self.assertEqual(report['fresh_candidate_mae'], report['candidate_mae'])

    def test_full_coverage_can_be_misleading(self):
        sample = rows()
        for i in range(10, 45):
            day, price, release = sample[i]
            sample[i] = (day, price, release + dt.timedelta(days=100))
        report = audit(sample, horizon=3, train_min=10)
        self.assertEqual(report['windows'], 23)
        self.assertEqual(report['fresh_origin_windows'], 12)
        self.assertEqual(report['fresh_origin_coverage_pct'], 100 * 12 / 23)
        self.assertEqual(report['quality_status'], 'insufficient_fresh_windows')
        self.assertEqual(report['status'], 'descriptive_only')

    def test_no_eligible_windows_has_null_error_metrics(self):
        sample = rows(30)
        for i in range(1, 30):
            day, price, release = sample[i]
            sample[i] = (day, price, release + dt.timedelta(days=200))
        report = audit(sample, horizon=3, train_min=10)
        self.assertEqual(report['fresh_origin_windows'], 0)
        self.assertIsNone(report['fresh_candidate_mae'])
        self.assertEqual(report['fresh_origin_coverage_pct'], 0)

    def test_zero_baseline_error_never_divides_by_zero(self):
        sample = [(d, 2000.0, t) for d, _, t in rows(100)]
        report = audit(sample, horizon=3, train_min=10)
        self.assertIsNone(report['fresh_improvement_pct'])
        self.assertEqual(report['fresh_baseline_mae'], 0)


if __name__ == '__main__':
    unittest.main()

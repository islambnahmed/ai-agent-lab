import datetime as dt
import math
import tempfile
import unittest
from pathlib import Path
from tools.gold_point_in_time import evaluate, load_rows, parse_timestamp

UTC = dt.timezone.utc

def rows(n=60):
    first = dt.date(2025, 1, 1)
    return [(first + dt.timedelta(days=i), 2000.0 + i, dt.datetime(2025, 1, 1, 20, tzinfo=UTC) + dt.timedelta(days=i)) for i in range(n)]

class PointInTimeTests(unittest.TestCase):
    def test_normal_evaluation(self):
        result = evaluate(rows(), horizon=3, train_min=10)
        self.assertEqual(result['status'], 'descriptive_only')
        self.assertGreater(result['windows'], 0)
        self.assertEqual(result['skipped'], 0)

    def test_no_future_leakage(self):
        original = rows()
        changed = original[:10] + [(d, p * 10, t) for d, p, t in original[10:]]
        a = evaluate(original, horizon=3, train_min=10)['results'][0]
        b = evaluate(changed, horizon=3, train_min=10)['results'][0]
        self.assertEqual(a['candidate'], b['candidate'])
        self.assertNotEqual(a['actual'], b['actual'])

    def test_late_release_ignored(self):
        sample = rows()
        d, p, t = sample[4]
        sample[4] = (d, p * 100, t + dt.timedelta(days=20))
        result = evaluate(sample, horizon=3, train_min=9)
        self.assertGreater(result['skipped'], 0)
        self.assertGreater(result['windows'], 0)
        self.assertNotEqual(result['results'][0]['last_observed_date'], sample[4][0].isoformat())

    def test_missing_availability_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'prices.csv'
            p.write_text('date,close\n2025-01-01,2000\n')
            with self.assertRaisesRegex(ValueError, 'available_at'):
                load_rows(p)

    def test_naive_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError, 'UTC offset'):
            parse_timestamp('2025-01-01T18:00:00')

    def test_duplicate_dates_rejected(self):
        sample = rows()
        sample[1] = (sample[0][0], sample[1][1], sample[1][2])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            evaluate(sample, horizon=2, train_min=10)

    def test_invalid_prices_rejected(self):
        sample = rows()
        sample[0] = (sample[0][0], math.nan, sample[0][2])
        with self.assertRaises(ValueError):
            evaluate(sample)

    def test_earlier_release_than_date_rejected(self):
        sample = rows()
        sample[0] = (sample[0][0], sample[0][1], sample[0][2] - dt.timedelta(days=1))
        with self.assertRaisesRegex(ValueError, 'release'):
            evaluate(sample)

    def test_target_already_known_skipped(self):
        sample = rows()
        d, p, t = sample[9]
        sample[9] = (d, p, t + dt.timedelta(days=40))
        result = evaluate(sample, horizon=3, train_min=10)
        self.assertGreater(result['skipped'], 0)

    def test_disjoint_windows(self):
        result = evaluate(rows(90), horizon=5, train_min=10)
        dates = [dt.date.fromisoformat(x['target_date']) for x in result['results']]
        self.assertTrue(all((b-a).days >= 5 for a, b in zip(dates, dates[1:])))

if __name__ == '__main__':
    unittest.main()

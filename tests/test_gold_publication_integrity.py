import datetime as dt
import unittest
from tools.gold_point_in_time import evaluate

UTC = dt.timezone.utc

def rows(n=80):
    first = dt.date(2025, 1, 1)
    return [(first + dt.timedelta(days=i), 100.0 * (1.01 ** i),
             dt.datetime(2025, 1, 1, 20, tzinfo=UTC) + dt.timedelta(days=i)) for i in range(n)]

class PublicationIntegrityTests(unittest.TestCase):
    def test_delayed_origin_never_moves_cutoff_forward(self):
        sample = rows()
        d, p, t = sample[11]
        sample[11] = (d, p, t + dt.timedelta(days=40))
        result = evaluate(sample, horizon=3, train_min=9)
        forecast = next(r for r in result['results'] if r['origin_date'] == d.isoformat())
        self.assertEqual(forecast['cutoff_utc'], '2025-01-13T00:00:00+00:00')
        self.assertLess(forecast['last_observed_date'], d.isoformat())

    def test_delayed_publication_does_not_inflate_drift(self):
        sample = rows()
        d, p, t = sample[5]
        sample[5] = (d, p, t + dt.timedelta(days=30))
        result = evaluate(sample, horizon=3, train_min=9)
        first = result['results'][0]
        target_index = (dt.date.fromisoformat(first['target_date']) - sample[0][0]).days
        self.assertAlmostEqual(first['candidate'], 100.0 * (1.01 ** target_index), places=7)

    def test_stale_inputs_are_audited(self):
        sample = rows()
        for i in range(10,45):
            d,p,t=sample[i]
            sample[i]=(d,p,t+dt.timedelta(days=100))
        result=evaluate(sample,horizon=3,train_min=10)
        self.assertEqual(result['coverage_pct'],100.0)
        self.assertEqual(result['stale_origin_windows'],11)
        self.assertEqual(sum(result['skip_reasons'].values()),result['skipped'])

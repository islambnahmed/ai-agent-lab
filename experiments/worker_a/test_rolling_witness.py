import datetime as dt
import unittest
from rolling_witness import issue_witness, assess_rolling_snapshot

START = dt.date(2026, 1, 1)
ROWS = [{'date': (START + dt.timedelta(days=i)).isoformat(), 'price': 4000 + i} for i in range(100)]
ISSUED = '2026-04-11T17:12:52Z'  # after last historical date (2026-04-10)
HASH = 'a' * 64


def issue(h=7):
    return issue_witness(ROWS, issued_at=ISSUED, source='Standard Bullion',
                         raw_sha256=HASH, snapshot_received_at='2026-04-11T17:10:00Z', horizon=h)


def extend(n=10):
    return ROWS + [{'date': (START + dt.timedelta(days=i)).isoformat(), 'price': 4000 + i} for i in range(100, 100 + n)]


def assess(w, rows):
    return assess_rolling_snapshot(w, rows, received_at='2026-04-23T08:00:00Z', raw_sha256='b' * 64)


class RollingWitnessTests(unittest.TestCase):
    def test_rolling_window_loses_original_prefix_but_validates_overlap(self):
        self.assertEqual(assess(issue(), extend()[15:])['status'], 'provisional')

    def test_actual_target_ordinal(self):
        x = assess(issue(), extend()[15:]); self.assertEqual(x['targetDate'], '2026-04-17'); self.assertEqual(x['actual'], '4106')

    def test_pending_when_horizon_not_mature(self):
        self.assertEqual(assess(issue(30), extend())['status'], 'pending')

    def test_detects_revision_in_tail(self):
        x = extend()[15:]; x[75] = dict(x[75], price=9999)
        self.assertEqual(assess(issue(), x)['reason'], 'historical_revision')

    def test_detects_missing_interior_tail_row(self):
        x = [r for r in extend()[15:] if r['date'] != ROWS[-5]['date']]
        self.assertEqual(assess(issue(), x)['reason'], 'interior_historical_gap')

    def test_quarantines_when_origin_missing(self):
        self.assertEqual(assess(issue(), extend()[100:])['status'], 'quarantined')

    def test_detects_tampered_witness(self):
        w = issue(); w['horizon'] = 30
        with self.assertRaisesRegex(ValueError, 'integrity'):
            assess(w, extend())

    def test_rejects_same_day_origin(self):
        with self.assertRaisesRegex(ValueError, 'completed'):
            issue_witness(ROWS, issued_at='2026-04-10T17:00:00Z', source='S', raw_sha256=HASH,
                          snapshot_received_at='2026-04-10T16:59:00Z', horizon=1)

    def test_rejects_invalid_price(self):
        x = list(ROWS); x[-1] = dict(x[-1], price=float('nan'))
        with self.assertRaisesRegex(ValueError, 'price'):
            issue_witness(x, issued_at=ISSUED, source='S', raw_sha256=HASH,
                          snapshot_received_at='2026-04-11T17:10:00Z', horizon=1)

    def test_no_same_day_target_maturity(self):
        x = extend(1)
        result = assess_rolling_snapshot(issue(1), x, received_at='2026-04-11T19:00:00Z', raw_sha256='b'*64)
        self.assertEqual(result['status'], 'pending')

    def test_ignores_older_revised_rows_outside_witness(self):
        x = extend(); x[0] = dict(x[0], price=111)
        self.assertEqual(assess(issue(), x[15:])['status'], 'provisional')

    def test_issue_does_not_store_raw_price(self):
        w = issue(); self.assertNotIn('price', str(w)); self.assertNotIn('4100', str(w))


if __name__ == '__main__':
    unittest.main()

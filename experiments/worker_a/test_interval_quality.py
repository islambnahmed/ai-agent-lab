import copy
import unittest
from interval_quality import interval_score, inspect_receipt, score_observation, aggregate

R = {'id': 'a'*64, 'horizon': 7, 'source': 'Provider A', 'issuedAt': '2026-10-12T17:00:00Z',
     'originDate': '2026-10-11', 'modelVersion': 'v2', 'point': 100., 'baseline': 100.,
     'lower': 95., 'upper': 105., 'targetDate': None}
O = {'source': 'Provider A', 'receivedAt': '2026-10-16T11:00:00Z', 'targetDate': '2026-10-15', 'actual': 103.}

class QualityTests(unittest.TestCase):
    def test_interval_inside(self): self.assertEqual(interval_score(100, 95, 105), 10)
    def test_interval_below(self): self.assertEqual(interval_score(90, 95, 105), 60)
    def test_interval_above(self): self.assertEqual(interval_score(110, 95, 105), 60)
    def test_narrow_beats_wide_when_covered(self): self.assertLess(interval_score(100, 99, 101), interval_score(100, 80, 120))
    def test_wide_beats_badly_missed_narrow(self): self.assertLess(interval_score(110, 80, 120), interval_score(110, 99, 101))
    def test_reject_inverted(self):
        with self.assertRaises(ValueError): interval_score(100, 105, 95)
    def test_reject_nan(self):
        with self.assertRaises(ValueError): interval_score(float('nan'), 95, 105)
    def test_reject_boolean(self):
        with self.assertRaises(ValueError): interval_score(True, 95, 105)
    def test_width_no_outcome(self):
        r=inspect_receipt(R);self.assertEqual(r['widthPctOfBaseline'],10);self.assertNotIn('coveragePct',r)
    def test_score_provisional(self):
        r=score_observation(R,O);self.assertEqual(r['intervalScore'],10);self.assertTrue(r['covered']);self.assertIn('provisional',r['status'])
    def test_reject_same_day(self):
        o={**O,'receivedAt':'2026-10-15T23:59:59Z'}
        with self.assertRaises(ValueError): score_observation(R,o)
    def test_reject_before_issue(self):
        o={**O,'receivedAt':'2026-10-12T16:00:00Z'}
        with self.assertRaises(ValueError): score_observation(R,o)
    def test_reject_source_mismatch(self):
        with self.assertRaises(ValueError): score_observation(R,{**O,'source':'Provider B'})
    def test_reject_target_mismatch(self):
        with self.assertRaises(ValueError): score_observation({**R,'targetDate':'2026-10-14'},O)
    def test_reject_non_utc_origin_issue(self):
        with self.assertRaises(ValueError): inspect_receipt({**R,'issuedAt':'2026-10-12T17:00:00'})
    def test_reject_duplicate_receipts(self):
        s=score_observation(R,O)
        with self.assertRaises(ValueError): aggregate([s,s])
    def test_reject_cross_horizon_pool(self):
        s=score_observation(R,O)
        with self.assertRaises(ValueError): aggregate([s,{**s,'id':'b'*64,'horizon':30}])
    def test_reject_no_outcomes(self):
        with self.assertRaises(ValueError): aggregate([])
    def test_aggregate_provisional(self):
        s=score_observation(R,O);a=aggregate([s]);self.assertEqual(a['n'],1);self.assertEqual(a['coveragePct'],100);self.assertEqual(a['status'],'descriptive_provisional_only')
    def test_origin_after_issue_rejected(self):
        with self.assertRaises(ValueError): inspect_receipt({**R,'originDate':'2026-10-12'})

if __name__ == '__main__': unittest.main()

"""Regression, leakage, selection-bias and time-budget counterexample tests."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from time_budget_study import make_packets, evaluate_time


def audit(rows):
    return {'rows': [{'url': u, 'status': 'disallowed', 'organic_clicks_30d': clicks,
                      'segment': segment, 'matched_rule': f'Disallow: /{segment}/',
                      'intent_label': 'accidental'}
                     for u, clicks, segment in rows]}


def completed(packet, labels, times):
    p = json.loads(json.dumps(packet))
    for item in p['items']:
        u = item['url']
        item['label'] = labels[u]
        item['seconds'] = times[u]
        item['evidence_note'] = 'synthetic fixture assumption' if labels[u] != 'unknown' else ''
    return p


class TimeBudgetTests(unittest.TestCase):
    def setUp(self):
        self.report = audit([('/a', 100, 'A'), ('/b', 90, 'A'), ('/c', 80, 'A'), ('/d', 70, 'B')])
        self.packets = make_packets(self.report, 314159)
        self.labels = {'/a': 'intentional', '/b': 'accidental', '/c': 'intentional', '/d': 'accidental'}
        self.times = {'/a': 1, '/b': 1, '/c': 1, '/d': 100}
        self.a, self.b = (completed(p, self.labels, self.times) for p in self.packets)

    def test_packets_blind_and_deterministic(self):
        self.assertEqual(self.packets, make_packets(self.report, 314159))
        for p in self.packets:
            self.assertEqual({x['url'] for x in p['items']}, {'/a', '/b', '/c', '/d'})
            for item in p['items']:
                self.assertNotIn('organic_clicks_30d', item)
                self.assertNotIn('segment', item)
                self.assertNotIn('intent_label', item)
                self.assertEqual(item['label'], 'unknown')
                self.assertIsNone(item['seconds'])

    def test_fixed_k_preference_reverses_under_time_budget(self):
        # At K=3: round-robin A,D,B -> two positives, clicks A,B,C -> one.
        # At 6 reviewer-seconds: clicks A,B,C -> one; round-robin A then D too costly -> zero.
        result = evaluate_time(self.report, self.a, self.b, [6, 500])
        x = result['rankings']['clicks_desc']['at_seconds']['6']
        y = result['rankings']['segment_round_robin']['at_seconds']['6']
        self.assertEqual((x['reviewed'], x['confirmed_accidental']), (3, 1))
        self.assertEqual((y['reviewed'], y['confirmed_accidental']), (1, 0))
        self.assertEqual(result['agreement']['agreement_rate'], 1)

    def test_labels_cannot_affect_rankings_or_review_cost(self):
        a2, b2 = json.loads(json.dumps(self.a)), json.loads(json.dumps(self.b))
        for sheet in (a2, b2):
            for item in sheet['items']:
                item['label'] = 'unknown'
                item['evidence_note'] = ''
        x = evaluate_time(self.report, self.a, self.b, [6])
        y = evaluate_time(self.report, a2, b2, [6])
        for method in x['rankings']:
            xx = x['rankings'][method]['at_seconds']['6']
            yy = y['rankings'][method]['at_seconds']['6']
            self.assertEqual((xx['reviewed'], xx['spent_reviewer_seconds']),
                             (yy['reviewed'], yy['spent_reviewer_seconds']))

    def test_reject_missing_duplicate_extra_and_unmeasured_reviews(self):
        for mutation in ('missing', 'duplicate', 'extra', 'null_seconds'):
            with self.subTest(mutation=mutation):
                a = json.loads(json.dumps(self.a))
                if mutation == 'missing': a['items'].pop()
                elif mutation == 'duplicate': a['items'][1]['url'] = a['items'][0]['url']
                elif mutation == 'extra': a['items'][1]['url'] = '/outside'
                else: a['items'][0]['seconds'] = None
                with self.assertRaises(ValueError): evaluate_time(self.report, a, self.b, [6])

    def test_reject_bad_labels_time_notes_and_budgets(self):
        for value in (True, 0, -1, 1.5, 3601, '10'):
            with self.subTest(seconds=value):
                a = json.loads(json.dumps(self.a))
                a['items'][0]['seconds'] = value
                with self.assertRaises(ValueError): evaluate_time(self.report, a, self.b, [6])
        a = json.loads(json.dumps(self.a))
        a['items'][0]['evidence_note'] = ''
        with self.assertRaises(ValueError): evaluate_time(self.report, a, self.b, [6])
        for budget in ([0], [True], [], [1.0]):
            with self.assertRaises(ValueError): evaluate_time(self.report, self.a, self.b, budget)

    def test_unresolved_and_empty_candidate_behavior(self):
        a = json.loads(json.dumps(self.a))
        first = next(item for item in a['items'] if item['url'] == '/a')
        first['label'] = 'unknown'
        first['evidence_note'] = ''
        r = evaluate_time(self.report, a, self.b, [2])
        self.assertEqual(r['rankings']['clicks_desc']['at_seconds']['2']['unresolved'], 1)
        empty = {'rows': [{'url': '/allowed', 'status': 'allowed'}]}
        pa, pb = make_packets(empty, 1)
        e = evaluate_time(empty, pa, pb, [1])
        self.assertEqual(e['candidate_count'], 0)
        self.assertEqual(e['rankings']['clicks_desc']['at_seconds']['1']['reviewed'], 0)

    def test_disallow_overwrite_of_existing_review_packet(self):
        # CLI refuses overwrites, protecting manually entered labels and times.
        from time_budget_study import main
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            report = p / 'audit.json'
            report.write_text(json.dumps(self.report))
            main(['prepare', '--audit', str(report), '--seed', '3', '--output-dir', str(p / 'packets')])
            with self.assertRaises(SystemExit):
                main(['prepare', '--audit', str(report), '--seed', '3', '--output-dir', str(p / 'packets')])


if __name__ == '__main__':
    unittest.main()

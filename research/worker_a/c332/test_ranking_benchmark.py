"""Regression and counterexample tests for label-blind review ordering."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ranking_benchmark import candidates, rankings, agreement, evaluate, load_json

HERE = Path(__file__).parent


def row(url, clicks, segment='s', status='disallowed', **kwargs):
    return {'url': url, 'organic_clicks_30d': clicks, 'segment': segment, 'status': status, **kwargs}


class BenchmarkTests(unittest.TestCase):
    def test_clicks_and_segment_round_robin(self):
        r = [row('/a', 100, 'A'), row('/b', 90, 'A'), row('/c', 80, 'A'),
             row('/d', 50, 'B'), row('/e', 40, 'B')]
        o = rankings(candidates({'rows': r}))
        self.assertEqual(o['clicks_desc'], ['/a', '/b', '/c', '/d', '/e'])
        self.assertEqual(o['segment_round_robin'], ['/a', '/d', '/b', '/e', '/c'])

    def test_labels_cannot_change_order(self):
        r = {'rows': [row('/a', 100, 'A', intent_label='accidental'), row('/b', 10, 'B', intent_label='intentional')]}
        a = evaluate(r, {'/a': {'rater_a': 'accidental', 'rater_b': 'accidental'}}, [2])
        b = evaluate(r, {'/a': {'rater_a': 'intentional', 'rater_b': 'intentional'}}, [2])
        for method in a['rankings']:
            self.assertEqual(a['rankings'][method]['top_urls'], b['rankings'][method]['top_urls'])

    def test_bounds_keep_unknown_and_disagreement_unresolved(self):
        r = {'rows': [row('/a', 10), row('/b', 9), row('/c', 8), row('/d', 7)]}
        labels = {'/a': {'rater_a': 'accidental', 'rater_b': 'accidental'},
                  '/b': {'rater_a': 'intentional', 'rater_b': 'intentional'},
                  '/c': {'rater_a': 'accidental', 'rater_b': 'intentional'}}
        e = evaluate(r, labels, [4])
        x = e['rankings']['clicks_desc']['at_k']['4']
        self.assertEqual((x['confirmed_accidental'], x['confirmed_intentional'], x['unresolved']), (1, 1, 2))
        self.assertEqual((x['precision_lower_bound'], x['precision_upper_bound']), (.25, .75))

    def test_agreement_calculation(self):
        l = {'a': {'rater_a': 'accidental', 'rater_b': 'accidental'},
             'b': {'rater_a': 'intentional', 'rater_b': 'intentional'},
             'c': {'rater_a': 'accidental', 'rater_b': 'intentional'},
             'd': {'rater_a': 'unknown', 'rater_b': 'intentional'}}
        a = agreement(l)
        self.assertEqual(a['dual_known'], 3)
        self.assertEqual(a['agreement_rate'], 0.666667)
        self.assertAlmostEqual(a['cohen_kappa'], .4)

    def test_no_agreement_data_is_null(self):
        self.assertIsNone(agreement({'a': {'rater_a': 'unknown', 'rater_b': 'intentional'}})['cohen_kappa'])
        self.assertIsNone(agreement({'a': {'rater_a': 'intentional', 'rater_b': 'intentional'}})['cohen_kappa'])

    def test_zero_candidates(self):
        e = evaluate({'rows': [row('/a', 1, status='allowed')]}, {}, [5])
        self.assertEqual(e['candidate_count'], 0)
        self.assertIsNone(e['rankings']['clicks_desc']['at_k']['5']['precision_lower_bound'])

    def test_reject_unrelated_label(self):
        with self.assertRaisesRegex(ValueError, 'not in disallowed'):
            evaluate({'rows': [row('/a', 1, status='allowed')]}, {'/a': {'rater_a': 'accidental', 'rater_b': 'accidental'}})

    def test_reject_duplicate_url_and_bad_clicks(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            candidates({'rows': [row('/a', 1), row('/a', 2)]})
        for bad in [True, -1, 1.5, '10', 10**9 + 1]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                candidates({'rows': [row('/a', bad)]})

    def test_reject_bad_labels_and_k(self):
        r = {'rows': [row('/a', 1)]}
        for labels in [{'/a': {'rater_a': 'accidental'}}, {'/a': {'rater_a': 'fake', 'rater_b': 'unknown'}}]:
            with self.assertRaises(ValueError):
                evaluate(r, labels)
        for k in [[], [0], [True], [-1]]:
            with self.assertRaises(ValueError):
                evaluate(r, {}, k)

    def test_counterexample_where_balancing_is_worse(self):
        # The balanced strategy is not universally better: this inverse fixture
        # deliberately makes high-click pages true positives and other segments negatives.
        r = {'rows': [row('/a1', 100, 'A'), row('/a2', 90, 'A'), row('/a3', 80, 'A'),
                      row('/b1', 70, 'B'), row('/c1', 60, 'C')]}
        labels = {u: {'rater_a': ('accidental' if u.startswith('/a') else 'intentional'),
                      'rater_b': ('accidental' if u.startswith('/a') else 'intentional')}
                  for u in ['/a1', '/a2', '/a3', '/b1', '/c1']}
        e = evaluate(r, labels, [3])
        self.assertEqual(e['rankings']['clicks_desc']['at_k']['3']['confirmed_accidental'], 3)
        self.assertEqual(e['rankings']['segment_round_robin']['at_k']['3']['confirmed_accidental'], 1)

    def test_many_segments_with_long_tail(self):
        rows = ([{'url': f'/{i}', 'clicks': 50000-i, 'segment': f's{i}'} for i in range(10000)] +
                [{'url': f'/tail{i}', 'clicks': 10000-i, 'segment': 'tail'} for i in range(10000)])
        order = rankings(rows)['segment_round_robin']
        self.assertEqual(len(order), 20000)
        self.assertEqual(len(set(order)), 20000)

    def test_synthetic_fixture_cli_and_stress_counterexample(self):
        report = load_json(HERE / 'synthetic_audit.json')
        labels = load_json(HERE / 'synthetic_raters.json')
        result = evaluate(report, labels, [5, 10])
        self.assertEqual(result['candidate_count'], 15)
        self.assertGreater(result['rankings']['segment_round_robin']['at_k']['5']['confirmed_accidental'],
                           result['rankings']['clicks_desc']['at_k']['5']['confirmed_accidental'])
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / 'result.json'
            cp = subprocess.run([sys.executable, str(HERE / 'ranking_benchmark.py'),
                                 '--audit', str(HERE / 'synthetic_audit.json'),
                                 '--labels', str(HERE / 'synthetic_raters.json'),
                                 '--output', str(output), '--k', '5', '10'], capture_output=True, text=True)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            self.assertEqual(json.loads(output.read_text())['candidate_count'], 15)


if __name__ == '__main__':
    unittest.main()

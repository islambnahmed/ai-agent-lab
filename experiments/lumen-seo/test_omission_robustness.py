"""Regression tests for omission_robustness.py (synthetic observations)."""
import csv
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from omission_robustness import probe, main

A = 'https://example.org/a'
B = 'https://example.org/b'

def make(seq, query='query'):
    rows = {}
    for i, c in enumerate(seq):
        d = date(2026, 10, 1) + timedelta(days=i)
        if c == 'X':
            rows[(d, A)] = 30.
            rows[(d, B)] = 30.
        else:
            rows[(d, A if c == 'A' else B)] = 60.
    return {query: rows}

class Robustness(unittest.TestCase):
    def one(self, seq):
        return probe(make(seq))['queries'][0]

    def test_persistent_stable_eight_days(self):
        x = self.one('XXXXXXXX')
        self.assertEqual(x['baseline'], 'persistent_co_visibility')
        self.assertTrue(x['stable_under_any_single_row_omission'])
        self.assertEqual(x['probes_run'], 16)

    def test_borderline_overlap_fragile(self):
        x = self.one('XXA')
        self.assertEqual(x['baseline'], 'persistent_co_visibility')
        self.assertFalse(x['stable_under_any_single_row_omission'])
        self.assertGreater(x['different_labels'], 0)
        self.assertIn('mixed_or_sparse', x['outcomes'])

    def test_clean_handoff_fragile(self):
        x = self.one('AAAABBBB')
        self.assertEqual(x['baseline'], 'sequential_handoff_possible')
        self.assertFalse(x['stable_under_any_single_row_omission'])
        self.assertIn('mixed_or_sparse', x['outcomes'])

    def test_reversals_stable(self):
        x = self.one('ABABABAB')
        self.assertEqual(x['baseline'], 'repeated_dominance_reversals')
        self.assertTrue(x['stable_under_any_single_row_omission'])

    def test_single_secondary_row_drops_detection(self):
        x = self.one('AAAAAAAB')
        self.assertIn('not_detected', x['outcomes'])

    def test_zero_impressions_excluded(self):
        grouped = make('ABAB')
        grouped['query'][(date(2026, 10, 20), A)] = 0
        x = probe(grouped)['queries'][0]
        self.assertEqual(x['probes_run'], 4)

    def test_per_query_budget_fail_closed(self):
        x = probe(make('ABABAB'), max_rows_per_query=3)['queries'][0]
        self.assertEqual(x['status'], 'not_assessed_budget')
        self.assertNotIn('stable_under_any_single_row_omission', x)

    def test_total_budget_fail_closed(self):
        x = probe(make('ABABAB'), max_rows_total=3)['queries'][0]
        self.assertEqual(x['status'], 'not_assessed_budget')

    def test_bad_budget(self):
        with self.assertRaises(ValueError):
            probe(make('AB'), max_rows_total=0)

    def test_does_not_mutate_input(self):
        grouped = make('XXA')
        before = dict(grouped['query'])
        probe(grouped)
        self.assertEqual(before, grouped['query'])

    def test_deterministic(self):
        self.assertEqual(probe(make('XXA')), probe(make('XXA')))

    def test_query_order(self):
        grouped = {**make('AB', 'z'), **make('XXA', 'a')}
        self.assertEqual([x['query'] for x in probe(grouped)['queries']], ['a', 'z'])

    def test_cli_with_csv(self):
        import contextlib, io
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'gsc.csv'
            with path.open('w', newline='') as f:
                writer=csv.writer(f)
                writer.writerow(['date','query','page','clicks','impressions','position'])
                for (d,page), imp in make('XXA')['query'].items():
                    writer.writerow([d.isoformat(),'query',page,0,imp,5])
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = main([str(path)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out.getvalue())['queries'][0]['baseline'], 'persistent_co_visibility')

    def test_missing_file_returns_error(self):
        import contextlib, io
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['/does/not/exist.csv']), 2)

if __name__ == '__main__':
    unittest.main()

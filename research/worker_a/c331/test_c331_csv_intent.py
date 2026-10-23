"""Offline input provenance and analyst-label evaluation tests."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from offline_csv_intent_audit import import_inventory, evaluate_intent, run

ROOT = Path(__file__).parent
ROBOTS = ROOT.parent / 'c330' / 'example_robots.txt'


class CSVIntentTests(unittest.TestCase):
    def csv(self, text):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        p = Path(self.temp.name) / 'input.csv'
        p.write_text(text, encoding='utf-8')
        return p

    def read(self, text, start='2026-09-01', end='2026-09-30'):
        return import_inventory(self.csv(text), period_start=start, period_end=end)

    def test_gsc_import_and_manual_precision(self):
        r = run(csv_path=ROOT / 'example_gsc_pages.csv', origin='https://example.com',
                user_agent='Googlebot', robots_path=ROBOTS,
                period_start='2026-09-01', period_end='2026-09-30')
        self.assertEqual(r['summary']['disallowed'], 3)
        self.assertEqual(r['summary']['out_of_scope'], 1)
        self.assertEqual(r['summary']['unknown'], 1)
        self.assertEqual(r['intent_evaluation']['disallowed_with_known_intent'], 2)
        self.assertEqual(r['intent_evaluation']['labeled_review_precision'], 0.5)
        self.assertEqual(r['intent_evaluation']['known_intent_coverage'], 0.666667)
        self.assertEqual(r['intent_evaluation']['analyst_labeled_accidental_urls'],
                         ['https://example.com/private/products'])
        self.assertEqual(r['provenance']['period']['days_inclusive'], 30)

    def test_unlabeled_precision_is_null_not_perfect(self):
        result = {'rows': [{'url': '/private', 'status': 'disallowed'},
                           {'url': '/bad', 'status': 'unknown'},
                           {'url': 'https://elsewhere/a', 'status': 'out_of_scope'}]}
        e = evaluate_intent(result, {'/private': 'unknown', '/bad': 'accidental',
                                     'https://elsewhere/a': 'accidental'})
        self.assertIsNone(e['labeled_review_precision'])
        self.assertEqual(e['disallowed_unlabeled'], 1)

    def test_date_range_exactly_30_days_inclusive(self):
        for start, end in [('2026-09-01', '2026-09-29'), ('2026-09-01', '2026-10-01'),
                           ('2026-09-30', '2026-09-01'), ('2026-02-30', '2026-03-31')]:
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                self.read('url,organic_clicks_30d\n/a,2\n', start, end)
        items, _, _ = self.read('url,organic_clicks_30d\n/a,2\n')
        self.assertEqual(items[0]['organic_clicks_30d'], 2)

    def test_reject_ambiguous_headers_and_malformed_rows(self):
        for csv_text in ['url,organic_clicks_30d,Clicks\n/a,2,4\n',
                         'url,url,organic_clicks_30d\n/a,/b,2\n',
                         'url,organic_clicks_30d\n/a\n',
                         'url,organic_clicks_30d\n/a,2,extra\n',
                         'url,organic_clicks_30d\n']:
            with self.subTest(csv=csv_text), self.assertRaises(ValueError):
                self.read(csv_text)

    def test_reject_untrusted_click_values(self):
        for val in ['-1', '1.5', '1,000', 'true', '1e3', '1000000001', ' 10']:
            with self.subTest(val=val), self.assertRaises(ValueError):
                self.read(f'url,organic_clicks_30d\n/a,"{val}"\n')

    def test_reject_conflicting_or_exact_duplicates(self):
        for csv_text in ['url,organic_clicks_30d\n/a,2\n/a,3\n',
                         'url,organic_clicks_30d\n/a,2\n/a,2\n']:
            with self.subTest(csv=csv_text), self.assertRaises(ValueError):
                self.read(csv_text)

    def test_reject_invalid_intent_label(self):
        with self.assertRaises(ValueError):
            self.read('url,organic_clicks_30d,intent_label\n/a,2,confirmed_by_google\n')

    def test_utf8_bom_accepted(self):
        items, _, _ = self.read('\ufeffurl,organic_clicks_30d\n/a,0\n')
        self.assertEqual(items[0]['organic_clicks_30d'], 0)

    def test_cross_origin_does_not_count_in_intent_precision(self):
        path = self.csv('url,organic_clicks_30d,intent_label\nhttps://other.example/private/a,99,accidental\n'
                        '/private/a,5,intentional\n')
        r = run(csv_path=path, origin='https://example.com', user_agent='Googlebot',
                robots_path=ROBOTS, period_start='2026-09-01', period_end='2026-09-30')
        self.assertEqual(r['intent_evaluation']['labeled_review_precision'], 0)
        self.assertEqual(r['intent_evaluation']['labeled_intentional'], 1)
        self.assertEqual(r['summary']['out_of_scope'], 1)

    def test_cli_smoke(self):
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / 'result.json'
            cmd = [sys.executable, str(ROOT / 'offline_csv_intent_audit.py'),
                   '--origin', 'https://example.com', '--user-agent', 'Googlebot',
                   '--robots-file', str(ROBOTS), '--csv', str(ROOT / 'example_gsc_pages.csv'),
                   '--period-start', '2026-09-01', '--period-end', '2026-09-30',
                   '--output', str(dest)]
            cp = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            self.assertEqual(json.loads(dest.read_text())['intent_evaluation']['labeled_accidental'], 1)


if __name__ == '__main__':
    unittest.main()

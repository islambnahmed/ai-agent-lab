"""Regression tests for conservative offline sitemap change triage."""
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from seo_sitemap_triage import build_queue, COLUMNS
from seo_sitemap_compare import compare
from collections import Counter

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'seo_sitemap_triage.py'


def sample():
    before = {
        'https://example.com/gone': Counter({('a.xml', ''): 1}),
        'https://example.com/moved': Counter({('a.xml', ''): 1}),
        'https://example.com/date': Counter({('a.xml', '2026-10-20'): 1}),
        'https://example.com/dupe': Counter({('a.xml', ''): 1}),
    }
    after = {
        'https://example.com/new': Counter({('a.xml', ''): 1}),
        'https://example.com/moved': Counter({('b.xml', ''): 1}),
        'https://example.com/date': Counter({('a.xml', '2026-10-21'): 1}),
        'https://example.com/dupe': Counter({('a.xml', ''): 2}),
    }
    result = compare(before, after)
    result['verification'] = {'status': 'complete_audit_csv_sha256_checked'}
    return result


class TriageTests(unittest.TestCase):
    def test_mixed_queue_priorities_and_actions(self):
        rows = build_queue(sample())
        self.assertEqual(len(rows), 5)
        self.assertEqual([(r[0], r[1]) for r in rows],
                         [('P1', 'removed'), ('P2', 'changed'), ('P2', 'changed'),
                          ('P3', 'added'), ('P3', 'changed')])
        self.assertEqual(rows[0][2], 'https://example.com/gone')
        self.assertEqual(rows[1][5:], [1, 2])
        self.assertIn('placement', rows[2][3])
        self.assertIn('lastmod', rows[4][3])

    def test_csv_only_evidence_remains_unverified(self):
        diff = sample()
        diff['verification']['status'] = 'csv_only_unverified'
        self.assertEqual({r[4] for r in build_queue(diff)}, {'csv_only_unverified'})

    def test_stable_order_with_reordered_input(self):
        diff = sample()
        first = build_queue(diff)
        diff['changed_existing_urls'].reverse()
        self.assertEqual(build_queue(diff), first)

    def test_rejects_bad_summary_without_partial_output(self):
        diff = sample()
        diff['summary']['removed_urls'] = 99
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'diff.json'
            path.write_text(json.dumps(diff), encoding='utf-8')
            p = subprocess.run([sys.executable, str(SCRIPT), '--diff', str(path)],
                               text=True, capture_output=True)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, '')

    def test_rejects_overlapping_urls_and_bad_detail_count(self):
        diff = sample()
        diff['added_urls'][0] = diff['removed_urls'][0]
        with self.assertRaises(ValueError):
            build_queue(diff)
        diff = sample()
        diff['changed_existing_urls'][0]['before'][0]['count'] = True
        with self.assertRaises(ValueError):
            build_queue(diff)

    def test_rejects_unknown_evidence_and_format(self):
        diff = sample()
        diff['verification']['status'] = 'live_verified'
        with self.assertRaises(ValueError):
            build_queue(diff)
        diff = sample()
        diff['kind'] = 'another_kind'
        with self.assertRaises(ValueError):
            build_queue(diff)

    def test_cli_csv_output_and_empty_queue(self):
        diff = sample()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'diff.json'
            path.write_text(json.dumps(diff), encoding='utf-8')
            p = subprocess.run([sys.executable, str(SCRIPT), '--diff', str(path)],
                               text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        parsed = list(csv.reader(io.StringIO(p.stdout)))
        self.assertEqual(parsed[0], COLUMNS)
        self.assertEqual(len(parsed), 6)
        diff = compare({}, {})
        diff['verification'] = {'status': 'csv_only_unverified'}
        self.assertEqual(build_queue(diff), [])


if __name__ == '__main__':
    unittest.main()

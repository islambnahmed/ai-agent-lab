"""Synthetic, network-free redirect-map checks."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from seo_redirect_map_audit import audit, canonical_key


def row(src, dst):
    return {'source_url': src, 'target_url': dst}


class RedirectAuditTests(unittest.TestCase):
    def test_conservative_default_port_and_host_case(self):
        self.assertEqual(canonical_key('HTTPS://EXAMPLE.COM:443/a?x=1'),
                         'https://example.com/a?x=1')
        self.assertNotEqual(canonical_key('https://example.com/a'),
                            canonical_key('https://example.com/a/'))

    def test_chain_and_cycle_and_self_redirect(self):
        result = audit([row('https://a.test/a', 'https://a.test/b'),
                        row('https://a.test/b', 'https://a.test/c'),
                        row('https://a.test/c', 'https://a.test/a'),
                        row('https://a.test/x', 'https://a.test/x')])
        self.assertEqual(result['issue_counts'],
                         {'redirect_chain': 3, 'redirect_cycle': 3, 'self_redirect': 1})
        self.assertEqual({i['row'] for i in result['issues'] if i['type']=='redirect_cycle'}, {2,3,4})

    def test_chain_without_cycle(self):
        result = audit([row('https://a.test/a', 'https://a.test/b'),
                        row('https://a.test/b', 'https://a.test/final')])
        self.assertEqual(result['issue_counts'], {'redirect_chain': 1})

    def test_duplicate_case_and_default_port(self):
        result = audit([row('https://a.test/a', 'https://a.test/b'),
                        row('HTTPS://A.TEST:443/a', 'https://a.test/c')])
        self.assertEqual(result['issue_counts'], {'conflicting_duplicate_source': 1})
        self.assertEqual(result['issues'][0]['first_row'], 2)

    def test_identical_duplicate_after_target_normalization(self):
        result = audit([row('https://a.test/a', 'HTTPS://A.TEST:443/b'),
                        row('HTTPS://A.TEST:443/a', 'https://a.test/b')])
        self.assertEqual(result['issue_counts'], {'duplicate_source': 1})
        self.assertEqual(result['issues'][0]['first_row'], 2)

    def test_conflicting_duplicate_preserves_first_wins_cycle(self):
        result = audit([row('https://a.test/a', 'https://a.test/b'),
                        row('https://a.test/a', 'https://a.test/c'),
                        row('https://a.test/b', 'https://a.test/a'),
                        row('https://a.test/c', 'https://a.test/final')])
        self.assertEqual(result['issue_counts'], {
            'conflicting_duplicate_source': 1,
            'redirect_chain': 2,
            'redirect_cycle': 2})
        conflict = [i for i in result['issues']
                    if i['type'] == 'conflicting_duplicate_source']
        self.assertEqual(conflict, [{'row': 3, 'type': 'conflicting_duplicate_source',
                                     'first_row': 2}])
        self.assertEqual({i['row'] for i in result['issues']
                          if i['type'] == 'redirect_cycle'}, {2, 4})
        self.assertNotIn('a.test', json.dumps(result))

    def test_invalid_url_no_leak(self):
        result = audit([row('https://user:secret@a.test/x', 'https://b.test/'),
                        row('https://a.test/path#fragment', 'https://b.test/'),
                        row('https://a.test/a', 'javascript:alert(1)')])
        self.assertEqual(result['issue_counts'], {'invalid_url': 3})
        self.assertNotIn('secret', json.dumps(result))

    def test_large_acyclic_graph_iterative(self):
        rows = [row(f'https://a.test/{i}', f'https://a.test/{i+1}') for i in range(3000)]
        result = audit(rows)
        self.assertEqual(result['issue_counts'], {'redirect_chain': 2999})

    def test_cli_clean_and_invalid_header(self):
        script = Path(__file__).resolve().parents[1] / 'tools' / 'seo_redirect_map_audit.py'
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'redirects.csv'
            with path.open('w', newline='', encoding='utf-8') as f:
                w=csv.DictWriter(f, fieldnames=['source_url','target_url'])
                w.writeheader()
                w.writerow(row('https://a.test/old', 'https://a.test/new'))
            ok = subprocess.run([sys.executable, str(script), '--map', str(path)],
                                capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(json.loads(ok.stdout)['issue_counts'], {})
            path.write_text('bad,header\na,b\n', encoding='utf-8')
            bad = subprocess.run([sys.executable, str(script), '--map', str(path)],
                                 capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)
            self.assertFalse(bad.stdout)


if __name__ == '__main__':
    unittest.main()

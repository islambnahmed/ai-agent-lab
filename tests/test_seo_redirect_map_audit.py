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


    def test_explicit_empty_query_preserved_in_duplicate_and_chain_checks(self):
        self.assertNotEqual(canonical_key('https://a.test/a?'),
                            canonical_key('https://a.test/a'))
        result = audit([row('https://a.test/a?', 'https://a.test/a'),
                        row('https://a.test/a', 'https://a.test/b')])
        self.assertEqual(result['unique_sources'], 2)
        self.assertEqual(result['issue_counts'], {'redirect_chain': 1})
        self.assertEqual(result['issues'][0]['row'], 2)

    def test_invalid_percent_escapes_and_empty_fragment_marker(self):
        bad = ['https://a.test/a%', 'https://a.test/a%2',
               'https://a.test/a%ZZ', 'https://a.test/a?q=%Q0',
               'https://a.test/a#']
        for url in bad:
            with self.subTest(url=url), self.assertRaises(ValueError):
                canonical_key(url)
        self.assertEqual(canonical_key('https://a.test/a%25'),
                         'https://a.test/a%25')
        result = audit([row(url, 'https://a.test/ok') for url in bad])
        self.assertEqual(result['issue_counts'], {'invalid_url': len(bad)})
        self.assertNotIn('a.test', json.dumps(result))

    def test_unicode_whitespace_and_c1_controls_are_invalid(self):
        # Previously accepted because only ASCII whitespace and DEL were checked.
        bad = ['https://a.test/old\u00a0page',
               'https://a.test/old\u2003page',
               'https://a.test/old\u0085page',
               'https://a.test/old?x=\u009f']
        for url in bad:
            with self.subTest(url=url), self.assertRaises(ValueError):
                canonical_key(url)
        # Encoded spaces are preserved literally; do not over-normalize URLs.
        self.assertEqual(canonical_key('https://a.test/old%C2%A0page'),
                         'https://a.test/old%C2%A0page')
        result = audit([row(url, 'https://a.test/new') for url in bad])
        self.assertEqual(result['issue_counts'], {'invalid_url': len(bad)})
        self.assertNotIn('a.test', json.dumps(result))

    def test_explicit_empty_port_is_invalid_not_silently_normalized(self):
        for url in ('https://a.test:/old', 'https://[::1]:/old'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                canonical_key(url)
        self.assertEqual(canonical_key('https://a.test:443/old'),
                         'https://a.test/old')
        self.assertEqual(canonical_key('https://[::1]/old'),
                         'https://[::1]/old')
        result = audit([row('https://a.test:/old', 'https://a.test/old'),
                        row('https://a.test/old', 'https://a.test:/new')])
        self.assertEqual(result['issue_counts'], {'invalid_url': 2})
        self.assertNotIn('a.test', json.dumps(result))

    def test_conflicting_duplicates_keep_empty_query_target_distinct(self):
        result = audit([row('https://a.test/a', 'https://a.test/b?'),
                        row('https://a.test/a', 'https://a.test/b')])
        self.assertEqual(result['issue_counts'], {'conflicting_duplicate_source': 1})

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

    def test_cli_uses_physical_line_numbers_after_multiline_csv(self):
        script = Path(__file__).resolve().parents[1] / 'tools' / 'seo_redirect_map_audit.py'
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'redirects.csv'
            # Record 1 begins on line 2 but spans lines 2-3.
            # Record 2 begins on line 4; conflicting record 3 begins on line 5.
            path.write_text(
                'source_url,target_url\n'
                '"https://a.test/bad\nline",https://a.test/ok\n'
                'https://a.test/old,https://a.test/new\n'
                'https://a.test/old,https://a.test/other\n',
                encoding='utf-8')
            result = subprocess.run(
                [sys.executable, str(script), '--map', str(path)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['issue_counts'], {
                'invalid_url': 1, 'conflicting_duplicate_source': 1})
            self.assertEqual(report['issues'], [
                {'row': 2, 'type': 'invalid_url'},
                {'row': 5, 'type': 'conflicting_duplicate_source', 'first_row': 4}])
            self.assertNotIn('a.test', result.stdout)

    def test_cli_physical_line_numbers_after_blank_records(self):
        script = Path(__file__).resolve().parents[1] / 'tools' / 'seo_redirect_map_audit.py'
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'redirects.csv'
            path.write_text(
                'source_url,target_url\n'
                '\n'
                'https://a.test/old,https://a.test/new\n'
                '\n'
                'https://a.test/old,https://a.test/other\n',
                encoding='utf-8')
            result = subprocess.run(
                [sys.executable, str(script), '--map', str(path)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['issues'], [
                {'row': 5, 'type': 'conflicting_duplicate_source', 'first_row': 3}])
            self.assertNotIn('a.test', result.stdout)

    def test_cli_preserves_malformed_extra_field_detection(self):
        script = Path(__file__).resolve().parents[1] / 'tools' / 'seo_redirect_map_audit.py'
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'redirects.csv'
            path.write_text('source_url,target_url\n'
                            'https://a.test/a,https://a.test/b,extra\n',
                            encoding='utf-8')
            result = subprocess.run(
                [sys.executable, str(script), '--map', str(path)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)['issues'],
                             [{'row': 2, 'type': 'malformed_row'}])

    def test_cli_input_error_does_not_expose_private_file_path(self):
        script = Path(__file__).resolve().parents[1] / 'tools' / 'seo_redirect_map_audit.py'
        with tempfile.TemporaryDirectory() as td:
            # OSError normally includes the missing path in its message.
            private_path = Path(td) / 'private_client_migration_map.csv'
            result = subprocess.run(
                [sys.executable, str(script), '--map', str(private_path)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            self.assertIn('invalid or unreadable input', result.stderr)
            self.assertNotIn('private_client_migration_map.csv', result.stderr)
            self.assertNotIn(td, result.stderr)

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

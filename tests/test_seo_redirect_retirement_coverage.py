"""Synthetic, network-free tests for redirect retirement coverage."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from seo_redirect_retirement_coverage import coverage, read_retiring

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'seo_redirect_retirement_coverage.py'


def row(src, dst):
    return {'source_url': src, 'target_url': dst}


class RetirementCoverageTests(unittest.TestCase):
    def test_missing_and_unlisted_are_separate_with_physical_lines(self):
        retiring = [(2, 'https://a.test/old'), (5, 'https://a.test/missing')]
        mapping = [row('https://a.test/old', 'https://a.test/new'),
                   row('https://a.test/other', 'https://a.test/other-new')]
        report = coverage(retiring, mapping, [3, 8])
        self.assertEqual(report['status'], 'complete')
        self.assertEqual(report['issues'], [
            {'row': 5, 'type': 'unmapped_retiring_url'},
            {'row': 8, 'type': 'unlisted_redirect_source'}])
        self.assertNotIn('a.test', json.dumps(report))

    def test_duplicate_inventory_and_canonical_equivalence(self):
        retiring = [(2, 'https://A.TEST:443/old'),
                    (4, 'https://a.test/old')]
        mapping = [row('https://a.test/old', 'https://a.test/new')]
        report = coverage(retiring, mapping, [2])
        self.assertEqual(report['issue_counts'], {'duplicate_retiring_url': 1})
        self.assertEqual(report['issues'][0]['first_row'], 2)
        self.assertEqual(report['unique_retiring_urls'], 1)

    def test_conflict_self_redirect_and_cycle_block_instead_of_false_success(self):
        retiring = [(2, 'https://a.test/a')]
        maps = [
            [row('https://a.test/a', 'https://a.test/b'),
             row('https://a.test/a', 'https://a.test/c')],
            [row('https://a.test/a', 'https://a.test/a')],
            [row('https://a.test/a', 'https://a.test/b'),
             row('https://a.test/b', 'https://a.test/a')],
        ]
        for mapping in maps:
            with self.subTest(mapping=mapping):
                report = coverage(retiring, mapping, list(range(2, 2+len(mapping))))
                self.assertEqual(report['status'], 'blocked')
                self.assertNotIn('issues', report)
                self.assertNotIn('a.test', json.dumps(report))

    def test_chain_is_warning_not_coverage_failure(self):
        retiring = [(2, 'https://a.test/a'), (3, 'https://a.test/b')]
        mapping = [row('https://a.test/a', 'https://a.test/b'),
                   row('https://a.test/b', 'https://a.test/final')]
        report = coverage(retiring, mapping, [2, 3])
        self.assertEqual(report['status'], 'complete')
        self.assertEqual(report['issue_counts'], {})
        self.assertEqual(report['map_issue_counts'], {'redirect_chain': 1})

    def test_cli_multiline_and_blank_line_positions_and_no_urls(self):
        with tempfile.TemporaryDirectory() as td:
            retirement = Path(td) / 'retiring.csv'
            redirects = Path(td) / 'map.csv'
            retirement.write_text(
                'url\n'
                '"https://a.test/bad\nline"\n', encoding='utf-8')
            redirects.write_text(
                'source_url,target_url\n'
                'https://a.test/other,https://a.test/new\n', encoding='utf-8')
            bad = subprocess.run([sys.executable, str(SCRIPT),
                                  '--retiring', str(retirement), '--map', str(redirects)],
                                 capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(bad.stdout, '')
            self.assertNotIn('a.test', bad.stderr)

            retirement.write_text(
                'url\n\nhttps://a.test/old\n'
                'https://a.test/missing\n', encoding='utf-8')
            redirects.write_text(
                'source_url,target_url\n'
                'https://a.test/old,https://a.test/new\n', encoding='utf-8')
            good = subprocess.run([sys.executable, str(SCRIPT),
                                   '--retiring', str(retirement), '--map', str(redirects)],
                                  capture_output=True, text=True)
            self.assertEqual(good.returncode, 1, good.stderr)
            report = json.loads(good.stdout)
            self.assertEqual(report['issues'],
                             [{'row': 4, 'type': 'unmapped_retiring_url'}])
            self.assertNotIn('a.test', good.stdout)

    def test_empty_inventory_is_not_misreported_as_complete(self):
        with tempfile.TemporaryDirectory() as td:
            retirement = Path(td) / 'retiring.csv'
            retirement.write_text('url\n\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'empty'):
                read_retiring(retirement)

    def test_invalid_map_blocks_cli_without_exposing_urls(self):
        with tempfile.TemporaryDirectory() as td:
            retirement = Path(td) / 'retiring.csv'
            redirects = Path(td) / 'map.csv'
            retirement.write_text('url\nhttps://a.test/a\n', encoding='utf-8')
            redirects.write_text('source_url,target_url\n'
                                 'https://a.test/a,https://a.test/a\n',
                                 encoding='utf-8')
            proc = subprocess.run([sys.executable, str(SCRIPT),
                                   '--retiring', str(retirement), '--map', str(redirects)],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertEqual(json.loads(proc.stdout)['status'], 'blocked')
            self.assertNotIn('a.test', proc.stdout)


if __name__ == '__main__':
    unittest.main()

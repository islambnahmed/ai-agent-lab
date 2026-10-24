"""Offline regressions for sitemap CSV inventory comparison."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from seo_sitemap_compare import compare, load_inventory

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'seo_sitemap_compare.py'
COLUMNS = ['source_sitemap', 'normalized_url', 'lastmod', 'duplicate']


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, filename, rows):
        path = self.root / filename
        with path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNS)
            writer.writerows(rows)
        return path

    def cli(self, before, after):
        return subprocess.run([sys.executable, str(SCRIPT), '--before', str(before),
                               '--after', str(after)], text=True, capture_output=True)

    def test_added_removed_and_changed_source_lastmod_and_duplicates(self):
        a = self.write('old.csv', [
            ['a.xml', 'https://example.com/keep', '2026-10-20', 'false'],
            ['a.xml', 'https://example.com/remove', '', 'false'],
            ['a.xml', 'https://example.com/change', '2026-10-20', 'false'],
        ])
        b = self.write('new.csv', [
            ['b.xml', 'https://example.com/change', '2026-10-21', 'false'],
            ['b.xml', 'https://example.com/change', '2026-10-21', 'true'],
            ['a.xml', 'https://example.com/keep', '2026-10-20', 'false'],
            ['a.xml', 'https://example.com/add', '', 'false'],
        ])
        p = self.cli(a, b)
        self.assertEqual(p.returncode, 1, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data['added_urls'], ['https://example.com/add'])
        self.assertEqual(data['removed_urls'], ['https://example.com/remove'])
        self.assertEqual(data['summary']['changed_existing_urls'], 1)
        self.assertEqual(data['changed_existing_urls'][0]['after'][0]['count'], 2)
        self.assertEqual(data['summary']['before_rows'], 3)
        self.assertEqual(data['summary']['after_rows'], 4)

    def test_row_order_and_first_duplicate_marker_do_not_change_inventory(self):
        a = self.write('old.csv', [
            ['a.xml', 'https://example.com/x', '', 'false'],
            ['b.xml', 'https://example.com/x', '', 'true'],
        ])
        b = self.write('new.csv', [
            ['b.xml', 'https://example.com/x', '', 'false'],
            ['a.xml', 'https://example.com/x', '', 'true'],
        ])
        self.assertEqual(self.cli(a, b).returncode, 0)
        self.assertEqual(compare(load_inventory(a), load_inventory(b))['summary']['changed_existing_urls'], 0)

    def test_deterministic_output(self):
        a = self.write('old.csv', [['a.xml', 'https://example.com/z', '', 'false']])
        b = self.write('new.csv', [['b.xml', 'https://example.com/z', '', 'false']])
        self.assertEqual(self.cli(a, b).stdout, self.cli(a, b).stdout)

    def test_bad_schema_and_malformed_row_fail_without_false_diff(self):
        a = self.write('old.csv', [['a.xml', 'https://example.com/a', '', 'false']])
        b = self.root / 'bad.csv'
        b.write_text('url\nhttps://example.com/a\n', encoding='utf-8')
        p = self.cli(a, b)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, '')
        b.write_text(','.join(COLUMNS) + '\na.xml,https://example.com/a\n', encoding='utf-8')
        self.assertEqual(self.cli(a, b).returncode, 2)

    def test_missing_and_invalid_marker_rejected(self):
        a = self.write('old.csv', [['a.xml', 'https://example.com/a', '', 'false']])
        b = self.root / 'missing.csv'
        self.assertEqual(self.cli(a, b).returncode, 2)
        b = self.write('bad.csv', [['a.xml', 'https://example.com/a', '', 'yes']])
        self.assertEqual(self.cli(a, b).returncode, 2)


    def test_missing_or_repeated_first_occurrence_marker_rejected(self):
        a = self.write('old.csv', [
            ['a.xml', 'https://example.com/x', '', 'false'],
        ])
        b = self.write('bad.csv', [
            ['a.xml', 'https://example.com/x', '', 'false'],
            ['b.xml', 'https://example.com/x', '', 'false'],
        ])
        result = self.cli(a, b)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stdout, '')
        b = self.write('bad.csv', [
            ['a.xml', 'https://example.com/x', '', 'true'],
        ])
        result = self.cli(a, b)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stdout, '')

    def test_valid_first_marker_can_appear_after_duplicate_row(self):
        a = self.write('old.csv', [
            ['a.xml', 'https://example.com/x', '', 'false'],
            ['b.xml', 'https://example.com/x', '', 'true'],
        ])
        b = self.write('new.csv', [
            ['b.xml', 'https://example.com/x', '', 'true'],
            ['a.xml', 'https://example.com/x', '', 'false'],
        ])
        result = self.cli(a, b)
        self.assertEqual(result.returncode, 0, result.stderr)



    def export_snapshot(self, label, pages, *, base_url='https://example.com/',
                        as_of='2026-10-24', missing_child=False):
        """Exercise the real exporter rather than inventing report metadata."""
        folder = self.root / label
        folder.mkdir()
        namespace = 'http://www.sitemaps.org/schemas/sitemap/0.9'
        urlset = '<urlset xmlns="' + namespace + '">' + ''.join(
            '<url><loc>' + base_url + page + '</loc></url>' for page in pages
        ) + '</urlset>'
        if missing_child:
            (folder / 'sitemap.xml').write_text(
                '<sitemapindex xmlns="' + namespace + '">'
                '<sitemap><loc>' + base_url + 'child.xml</loc></sitemap>'
                '<sitemap><loc>' + base_url + 'missing.xml</loc></sitemap>'
                '</sitemapindex>', encoding='utf-8')
            (folder / 'child.xml').write_text(urlset, encoding='utf-8')
        else:
            (folder / 'sitemap.xml').write_text(urlset, encoding='utf-8')
        csv_path = self.root / (label + '.csv')
        report_path = self.root / (label + '.json')
        audit_script = SCRIPT.with_name('seo_sitemap_audit.py')
        p = subprocess.run([sys.executable, str(audit_script), '--root', str(folder),
                            '--base-url', base_url, '--as-of', as_of,
                            '--urls-csv', str(csv_path)], capture_output=True, text=True)
        self.assertIn(p.returncode, (0, 1), p.stderr)
        report_path.write_text(p.stdout, encoding='utf-8')
        return csv_path, report_path, p.returncode

    def verified_cli(self, old, new):
        return subprocess.run([sys.executable, str(SCRIPT),
                               '--before', str(old[0]), '--after', str(new[0]),
                               '--before-report', str(old[1]),
                               '--after-report', str(new[1])],
                              capture_output=True, text=True)

    def test_clean_bound_reports_verify_real_export_and_detect_removal(self):
        old = self.export_snapshot('old', ['keep', 'removed'])
        new = self.export_snapshot('new', ['keep'])
        self.assertEqual(old[2], 0)
        self.assertEqual(new[2], 0)
        p = self.verified_cli(old, new)
        self.assertEqual(p.returncode, 1, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data['removed_urls'], ['https://example.com/removed'])
        self.assertEqual(data['verification']['status'], 'clean_audit_csv_sha256_checked')
        self.assertEqual(data['verification']['base_url'], 'https://example.com/')

    def test_missing_sitemap_child_rejects_apparent_removals(self):
        old = self.export_snapshot('old', ['keep', 'removed'])
        new = self.export_snapshot('new', ['keep'], missing_child=True)
        self.assertEqual(new[2], 1)
        p = self.verified_cli(old, new)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertEqual(p.stdout, '')
        self.assertIn('not complete', p.stderr)

    def test_changed_csv_bytes_rejected_even_with_same_row_count(self):
        old = self.export_snapshot('old', ['keep', 'removed'])
        new = self.export_snapshot('new', ['keep', 'removed'])
        csv_path = new[0]
        csv_path.write_text(csv_path.read_text(encoding='utf-8').replace(
            'https://example.com/keep', 'https://example.com/kept'), encoding='utf-8')
        p = self.verified_cli(old, new)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn('SHA-256', p.stderr)

    def test_mismatched_site_and_reversed_audit_dates_rejected(self):
        old = self.export_snapshot('old', ['keep'], as_of='2026-10-24')
        new = self.export_snapshot('new', ['keep'], base_url='https://another.example/')
        p = self.verified_cli(old, new)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn('origins differ', p.stderr)
        new = self.export_snapshot('earlier', ['keep'], as_of='2026-10-23')
        p = self.verified_cli(old, new)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn('after audit date', p.stderr)

    def test_csv_only_mode_is_explicitly_unverified(self):
        old = self.write('old.csv', [['a.xml', 'https://example.com/a', '', 'false']])
        new = self.write('new.csv', [['a.xml', 'https://example.com/a', '', 'false']])
        p = self.cli(old, new)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)['verification']['status'], 'csv_only_unverified')
        p = subprocess.run([sys.executable, str(SCRIPT), '--before', str(old),
                            '--after', str(new), '--before-report', str(self.root / 'x.json')],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, '')




if __name__ == '__main__':
    unittest.main()

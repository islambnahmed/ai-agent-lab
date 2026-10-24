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


if __name__ == '__main__':
    unittest.main()

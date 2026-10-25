import datetime as dt
import csv
import gzip
from pathlib import Path
import sys
import json
import subprocess
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from seo_sitemap_audit import audit, _local_target, _normalize_url

NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
TODAY = dt.date(2026, 10, 24)


def urlset(*items):
    return f'<urlset xmlns="{NS}">' + ''.join(f'<url><loc>{url}</loc>' + (f'<lastmod>{lastmod}</lastmod>' if lastmod is not None else '') + '</url>' for url,lastmod in items) + '</urlset>'


def index(*urls):
    return f'<sitemapindex xmlns="{NS}">' + ''.join(f'<sitemap><loc>{url}</loc></sitemap>' for url in urls) + '</sitemapindex>'


class SitemapAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, contents):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding='utf-8')

    def run_audit(self, start='sitemap.xml'):
        return audit(self.root, start, 'https://example.com/', TODAY)

    def codes(self, start='sitemap.xml'):
        return [i['code'] for i in self.run_audit(start)['issues']]

    def test_valid_nested_index_and_gzip(self):
        self.write('sitemap.xml', index('https://example.com/a.xml', 'https://example.com/sub/b.xml.gz'))
        self.write('a.xml', urlset(('https://example.com/a', '2026-10-20')))
        target = self.root / 'sub/b.xml.gz'
        target.parent.mkdir()
        target.write_bytes(gzip.compress(urlset(('https://example.com/b', '2026-10-20T10:00:00+00:00')).encode()))
        report = self.run_audit()
        self.assertEqual(report['summary'], {'sitemaps':3,'urlsets':2,'indexes':1,'urls':2,'unique_urls':2,'issues':0})

    def test_duplicates_across_sitemaps_normalized(self):
        self.write('sitemap.xml', index('https://example.com/a.xml','https://example.com/b.xml'))
        self.write('a.xml', urlset(('HTTPS://EXAMPLE.COM:443/a#frag', None)))
        self.write('b.xml', urlset(('https://example.com/a', None)))
        self.assertEqual(self.codes(), ['duplicate_url'])

    def test_future_and_invalid_lastmod(self):
        self.write('sitemap.xml', urlset(('https://example.com/a','2026-10-25'),('https://example.com/b','yesterday'),('https://example.com/c','2026-10-24T23:00:00-05:00')))
        self.assertEqual(sorted(self.codes()), ['future_lastmod','future_lastmod','invalid_lastmod'])

    def test_missing_child_and_index_cycle(self):
        self.write('sitemap.xml', index('https://example.com/missing.xml','https://example.com/sitemap.xml'))
        self.assertEqual(sorted(self.codes()), ['index_cycle','missing_sitemap'])

    def test_index_external_and_encoded_traversal_rejected(self):
        self.write('sitemap.xml', index('https://evil.example/x.xml','https://example.com/%2e%2e/secret.xml'))
        self.assertEqual(self.codes(), ['unmapped_index_loc','unmapped_index_loc'])
        self.assertIsNone(_local_target('https://example.com/%2e%2e/secret.xml','https://example.com/',self.root.resolve()))

    def test_malformed_xml_and_unsafe_doctype(self):
        self.write('sitemap.xml','<urlset>')
        self.assertEqual(self.codes(), ['malformed_xml'])
        self.write('sitemap.xml',f'<!DOCTYPE urlset [<!ENTITY x "y">]><urlset xmlns="{NS}"/>')
        self.assertEqual(self.codes(), ['xml_declaration_unsafe'])

    def test_invalid_urls_wrong_host_and_missing_loc(self):
        self.write('sitemap.xml', f'<urlset xmlns="{NS}"><url><loc>javascript:alert(1)</loc></url><url><loc>https://other.com/</loc></url><url/></urlset>')
        self.assertEqual(sorted(self.codes()), ['invalid_url','missing_loc','off_host_url'])

    def test_unexpected_root_and_missing_start(self):
        self.write('sitemap.xml','<feed/>')
        self.assertEqual(self.codes(), ['unexpected_root'])
        self.assertEqual(self.codes('absent.xml'), ['missing_sitemap'])

    def test_url_normalization_and_no_network(self):
        self.assertEqual(_normalize_url('HTTPS://EXAMPLE.COM:443/x#frag'), 'https://example.com/x')
        self.assertIsNone(_normalize_url('https://user:pw@example.com/x'))
        self.assertIsNone(_normalize_url('not-a-url'))

    def test_wrong_namespace_entries_cannot_disappear_silently(self):
        self.write('sitemap.xml', f'<urlset xmlns="{NS}"><url xmlns="urn:wrong"><loc>https://example.com/a</loc></url></urlset>')
        self.assertEqual(self.codes(), ['wrong_entry_namespace'])
        self.write('sitemap.xml', f'<sitemapindex xmlns="{NS}"><sitemap xmlns="urn:wrong"><loc>https://example.com/a.xml</loc></sitemap></sitemapindex>')
        self.assertEqual(self.codes(), ['wrong_entry_namespace'])
        self.write('sitemap.xml', f'<urlset xmlns="{NS}"><url><loc>https://example.com/a</loc></url><url xmlns="urn:wrong"><loc>https://example.com/b</loc></url></urlset>')
        self.assertEqual(self.codes(), ['wrong_entry_namespace'])

    def test_unexpected_direct_children_cannot_hide_incomplete_inventory(self):
        # Fail closed: malformed direct entries cannot be silently omitted.
        self.write('sitemap.xml',
                   f'<urlset xmlns="{NS}"><url><loc>https://example.com/good</loc></url>'
                   f'<entry><loc>https://example.com/hidden</loc></entry></urlset>')
        report = self.run_audit()
        self.assertEqual(report['summary']['urls'], 1)
        self.assertEqual(self.codes(), ['unexpected_entry'])
        self.write('sitemap.xml',
                   f'<urlset xmlns="{NS}"><url><loc>https://example.com/good</loc></url>'
                   f'<other:entry xmlns:other="urn:other"><other:loc>https://example.com/hidden'
                   f'</other:loc></other:entry></urlset>')
        self.assertEqual(self.codes(), ['unexpected_entry'])
        self.write('sitemap.xml',
                   f'<sitemapindex xmlns="{NS}"><entry><loc>https://example.com/hidden.xml'
                   f'</loc></entry></sitemapindex>')
        self.assertEqual(self.codes(), ['unexpected_entry'])

    def test_unknown_entry_causes_nonzero_cli_even_with_csv_export(self):
        self.write('sitemap.xml',
                   f'<urlset xmlns="{NS}"><url><loc>https://example.com/good</loc></url>'
                   f'<entry><loc>https://example.com/hidden</loc></entry></urlset>')
        destination = self.root / 'inventory.csv'
        script = str(Path(__file__).resolve().parents[1] / 'tools/seo_sitemap_audit.py')
        result = subprocess.run([sys.executable, script, '--root', str(self.root),
                                 '--base-url', 'https://example.com/',
                                 '--as-of', '2026-10-24', '--urls-csv', str(destination)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual([i['code'] for i in json.loads(result.stdout)['issues']],
                         ['unexpected_entry'])
        with destination.open(newline='', encoding='utf-8') as handle:
            self.assertEqual([row['normalized_url'] for row in csv.DictReader(handle)],
                             ['https://example.com/good'])

    def test_mixed_scheme_same_host_is_reported(self):
        self.write('sitemap.xml', urlset(('http://example.com/a', None), ('https://example.com/b', None)))
        report = self.run_audit()
        self.assertEqual([i['code'] for i in report['issues']], ['off_origin_url'])
        self.assertEqual(report['summary']['urls'], 2)

    def test_corrupt_gzip_is_isolated(self):
        (self.root / 'sitemap.xml.gz').write_bytes(b'\x1f\x8bcorrupt')
        self.assertEqual(self.codes('sitemap.xml.gz'), ['unreadable_sitemap'])

    def test_cli_exit_status_and_deterministic_json(self):
        script = str(Path(__file__).resolve().parents[1] / 'tools/seo_sitemap_audit.py')
        args = [sys.executable, script, '--root', str(self.root), '--base-url', 'https://example.com', '--as-of', '2026-10-24']
        self.write('sitemap.xml', urlset(('https://example.com/a', '2026-10-20')))
        good = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(good.returncode, 0)
        self.assertEqual(json.loads(good.stdout)['summary']['urls'], 1)
        self.assertEqual(good.stdout, subprocess.run(args, capture_output=True, text=True).stdout)
        self.write('sitemap.xml', urlset(('https://example.com/a', '2026-10-25')))
        bad = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        self.assertEqual(json.loads(bad.stdout)['issues'][0]['code'], 'future_lastmod')

    def test_csv_export_is_a_real_url_inventory_including_duplicates(self):
        self.write('sitemap.xml', index('https://example.com/a.xml', 'https://example.com/b.xml'))
        self.write('a.xml', urlset(('https://example.com/one', '2026-10-20'),
                                   ('https://example.com/two', None)))
        self.write('b.xml', urlset(('HTTPS://EXAMPLE.COM:443/one#fragment', None)))
        destination = self.root / 'inventory.csv'
        script = str(Path(__file__).resolve().parents[1] / 'tools/seo_sitemap_audit.py')
        args = [sys.executable, script, '--root', str(self.root), '--base-url',
                'https://example.com/', '--as-of', '2026-10-24',
                '--urls-csv', str(destination)]
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)['summary']['unique_urls'], 2)
        with destination.open(newline='', encoding='utf-8') as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(rows, [
            {'source_sitemap':'a.xml', 'normalized_url':'https://example.com/one',
             'lastmod':'2026-10-20', 'duplicate':'false'},
            {'source_sitemap':'a.xml', 'normalized_url':'https://example.com/two',
             'lastmod':'', 'duplicate':'false'},
            {'source_sitemap':'b.xml', 'normalized_url':'https://example.com/one',
             'lastmod':'', 'duplicate':'true'},
        ])
        first = destination.read_bytes()
        self.assertEqual(subprocess.run(args, capture_output=True).returncode, 1)
        self.assertEqual(destination.read_bytes(), first)

    def test_csv_export_skips_invalid_loc_but_preserves_diagnostics(self):
        self.write('sitemap.xml', urlset(('javascript:bad', None),
                                         ('https://example.com/good', None)))
        destination = self.root / 'inventory.csv'
        script = str(Path(__file__).resolve().parents[1] / 'tools/seo_sitemap_audit.py')
        result = subprocess.run([sys.executable, script, '--root', str(self.root),
                                 '--base-url', 'https://example.com/',
                                 '--as-of', '2026-10-24', '--urls-csv', str(destination)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual([i['code'] for i in json.loads(result.stdout)['issues']], ['invalid_url'])
        with destination.open(newline='', encoding='utf-8') as handle:
            self.assertEqual([row['normalized_url'] for row in csv.DictReader(handle)],
                             ['https://example.com/good'])

    def test_csv_spreadsheet_formula_cells_are_escaped(self):
        self.write('sitemap.xml', index('https://example.com/=1+1.xml'))
        self.write('=1+1.xml', urlset(('https://example.com/page', '=1+1')))
        destination = self.root / 'inventory.csv'
        script = str(Path(__file__).resolve().parents[1] / 'tools/seo_sitemap_audit.py')
        result = subprocess.run([sys.executable, script, '--root', str(self.root),
                                 '--base-url', 'https://example.com/',
                                 '--as-of', '2026-10-24', '--urls-csv', str(destination)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual([i['code'] for i in json.loads(result.stdout)['issues']],
                         ['invalid_lastmod'])
        with destination.open(newline='', encoding='utf-8') as handle:
            row = list(csv.DictReader(handle))[0]
        self.assertEqual(row['source_sitemap'], "'=1+1.xml")
        self.assertEqual(row['lastmod'], "'=1+1")
        self.assertEqual(row['normalized_url'], 'https://example.com/page')

    def test_invalid_csv_configuration_does_not_replace_existing_output(self):
        self.write('sitemap.xml', urlset(('https://example.com/a', None)))
        destination = self.root / 'inventory.csv'
        destination.write_text('previous result', encoding='utf-8')
        script = str(Path(__file__).resolve().parents[1] / 'tools/seo_sitemap_audit.py')
        result = subprocess.run([sys.executable, script, '--root', str(self.root),
                                 '--base-url', 'https://example.com/',
                                 '--as-of', 'not-a-date', '--urls-csv', str(destination)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(destination.read_text(encoding='utf-8'), 'previous result')
        self.assertFalse(list(self.root.glob('.sitemap-audit-*.csv')))

    def test_csv_export_refuses_to_replace_input_sitemaps(self):
        self.write('sitemap.xml', urlset(('https://example.com/a', None)))
        original = (self.root / 'sitemap.xml').read_bytes()
        script = str(Path(__file__).resolve().parents[1] / 'tools/seo_sitemap_audit.py')
        args = [sys.executable, script, '--root', str(self.root),
                '--base-url', 'https://example.com/', '--as-of', '2026-10-24',
                '--urls-csv', str(self.root / 'sitemap.xml')]
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('must not end in .xml or .gz', result.stderr)
        self.assertEqual((self.root / 'sitemap.xml').read_bytes(), original)
        self.assertFalse(list(self.root.glob('.sitemap-audit-*.csv')))

        compressed = self.root / 'child.xml.gz'
        compressed.write_bytes(gzip.compress(urlset(('https://example.com/b', None)).encode()))
        before = compressed.read_bytes()
        args[-1] = str(compressed)
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(compressed.read_bytes(), before)
        self.assertFalse(list(self.root.glob('.sitemap-audit-*.csv')))

    def test_csv_export_rejects_non_csv_destination_even_with_replace(self):
        self.write('sitemap.xml', urlset(('https://example.com/a', None)))
        script = str(Path(__file__).resolve().parents[1] / 'tools/seo_sitemap_audit.py')
        for name in ('important.txt', 'notes.md', 'report'):
            with self.subTest(name=name):
                destination = self.root / name
                destination.write_text('preserve this content', encoding='utf-8')
                args = [sys.executable, script, '--root', str(self.root),
                        '--base-url', 'https://example.com/', '--as-of', '2026-10-24',
                        '--urls-csv', str(destination), '--replace-csv']
                result = subprocess.run(args, capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn('must end in .csv', result.stderr)
                self.assertEqual(destination.read_text(encoding='utf-8'),
                                 'preserve this content')
                self.assertFalse(list(self.root.glob('.sitemap-audit-*.csv')))

    def test_csv_export_does_not_clobber_different_existing_file_without_opt_in(self):
        self.write('sitemap.xml', urlset(('https://example.com/first', None)))
        destination = self.root / 'inventory.csv'
        destination.write_text('important existing data', encoding='utf-8')
        script = str(Path(__file__).resolve().parents[1] / 'tools/seo_sitemap_audit.py')
        args = [sys.executable, script, '--root', str(self.root),
                '--base-url', 'https://example.com/', '--as-of', '2026-10-24',
                '--urls-csv', str(destination)]
        blocked = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(blocked.returncode, 2, blocked.stderr)
        self.assertIn('--replace-csv', blocked.stderr)
        self.assertEqual(destination.read_text(encoding='utf-8'), 'important existing data')
        self.assertFalse(list(self.root.glob('.sitemap-audit-*.csv')))

        allowed = subprocess.run(args + ['--replace-csv'], capture_output=True, text=True)
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        with destination.open(newline='', encoding='utf-8') as stream:
            self.assertEqual([row['normalized_url'] for row in csv.DictReader(stream)],
                             ['https://example.com/first'])

        # Same bytes are idempotent, but a changed sitemap requires opt-in.
        self.assertEqual(subprocess.run(args, capture_output=True).returncode, 0)
        first_export = destination.read_bytes()
        self.write('sitemap.xml', urlset(('https://example.com/second', None)))
        changed = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(changed.returncode, 2, changed.stderr)
        self.assertEqual(destination.read_bytes(), first_export)
        self.assertFalse(list(self.root.glob('.sitemap-audit-*.csv')))
        self.assertEqual(subprocess.run(args + ['--replace-csv'],
                                        capture_output=True).returncode, 0)

    def test_limit_and_bad_configuration(self):
        self.write('sitemap.xml', index('https://example.com/a.xml'))
        self.write('a.xml', urlset(('https://example.com/a',None)))
        self.assertEqual(self.run_audit()['summary']['sitemaps'],2)
        self.assertIn('sitemap_limit', [i['code'] for i in audit(self.root,'sitemap.xml','https://example.com/',TODAY,max_sitemaps=1)['issues']])
        with self.assertRaises(ValueError):
            audit(self.root,'sitemap.xml','ftp://example.com/',TODAY)
        with self.assertRaises(ValueError):
            audit(self.root,'../sitemap.xml','https://example.com/',TODAY)


if __name__ == '__main__':
    unittest.main()

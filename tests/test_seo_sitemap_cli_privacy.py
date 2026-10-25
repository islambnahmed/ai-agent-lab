"""Offline regression: CLI errors must not disclose customer paths or URL values."""
import contextlib
import csv
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import seo_sitemap_audit
import seo_sitemap_budget_eval
import seo_sitemap_field_score
import seo_sitemap_triage


def capture_main(module, args):
    stream = io.StringIO()
    with contextlib.redirect_stderr(stream):
        code = module.main(args)
    return code, stream.getvalue()


class SitemapCliPrivacyTests(unittest.TestCase):
    def test_compare_missing_inventory_path_is_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            private = Path(tmp) / 'CUSTOMER_SECRET_873_missing.csv'
            result = subprocess.run(
                [sys.executable, str(ROOT / 'tools/seo_sitemap_compare.py'),
                 '--before', str(private), '--after', str(private)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertNotIn('CUSTOMER_SECRET_873', result.stderr + result.stdout)
            self.assertNotIn(str(private), result.stderr + result.stdout)

    def test_compare_duplicate_marker_error_redacts_raw_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / 'before.csv'
            after = Path(tmp) / 'after.csv'
            url = 'https://example.test/PRIVATE_URL_SENTINEL_873'
            for dest, rows in ((before, 2), (after, 1)):
                with dest.open('w', newline='', encoding='utf-8') as handle:
                    writer = csv.writer(handle)
                    writer.writerow(['source_sitemap', 'normalized_url', 'lastmod', 'duplicate'])
                    for _ in range(rows):
                        writer.writerow(['sitemap.xml', url, '', 'false'])
            result = subprocess.run(
                [sys.executable, str(ROOT / 'tools/seo_sitemap_compare.py'),
                 '--before', str(before), '--after', str(after)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertNotIn('PRIVATE_URL_SENTINEL_873', result.stderr + result.stdout)
            self.assertIn('inconsistent duplicate markers', result.stderr)

    def test_audit_os_error_does_not_expose_export_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            private = Path(tmp) / 'CUSTOMER_SECRET_873_export.csv'
            error = OSError(13, 'permission denied', str(private))
            with patch.object(seo_sitemap_audit.tempfile, 'NamedTemporaryFile', side_effect=error):
                code, stderr = capture_main(
                    seo_sitemap_audit,
                    ['--root', tmp, '--base-url', 'https://example.test/',
                     '--urls-csv', str(private)])
            self.assertEqual(code, 2)
            self.assertNotIn('CUSTOMER_SECRET_873', stderr)
            self.assertIn('operation failed', stderr)

    def test_triage_os_error_does_not_expose_diff_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            private = Path(tmp) / 'CUSTOMER_SECRET_873_diff.json'
            private.write_text('{}', encoding='utf-8')
            error = OSError(13, 'permission denied', str(private))
            with patch.object(Path, 'read_text', side_effect=error):
                code, stderr = capture_main(seo_sitemap_triage, ['--diff', str(private)])
            self.assertEqual(code, 2)
            self.assertNotIn('CUSTOMER_SECRET_873', stderr)
            self.assertIn('input read failed', stderr)

    def test_budget_os_error_does_not_expose_queue_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            private = Path(tmp) / 'CUSTOMER_SECRET_873_queue.csv'
            labels = Path(tmp) / 'labels.csv'
            private.write_text('', encoding='utf-8')
            labels.write_text('', encoding='utf-8')
            error = OSError(13, 'permission denied', str(private))
            with patch.object(Path, 'open', side_effect=error):
                code, stderr = capture_main(
                    seo_sitemap_budget_eval,
                    ['--queue', str(private), '--labels', str(labels), '--budget', '1'])
            self.assertEqual(code, 2)
            self.assertNotIn('CUSTOMER_SECRET_873', stderr)
            self.assertIn('input read failed', stderr)

    def test_field_score_os_error_does_not_expose_reference_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            private = Path(tmp) / 'CUSTOMER_SECRET_873_refs.csv'
            sessions = Path(tmp) / 'sessions.csv'
            decisions = Path(tmp) / 'decisions.csv'
            for path in (private, sessions, decisions):
                path.write_text('', encoding='utf-8')
            error = OSError(13, 'permission denied', str(private))
            with patch.object(Path, 'open', side_effect=error):
                code, stderr = capture_main(
                    seo_sitemap_field_score,
                    ['--references', str(private), '--sessions', str(sessions),
                     '--decisions', str(decisions)])
            self.assertEqual(code, 2)
            self.assertNotIn('CUSTOMER_SECRET_873', stderr)
            self.assertIn('input read failed', stderr)


if __name__ == '__main__':
    unittest.main()

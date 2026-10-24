"""Offline regression tests; no GitHub network requests."""
import base64
import json
import tempfile
import unittest
from pathlib import Path
from publication_anchor import audit, assess

SHA = 'a' * 40
STAMP = '2026-10-12T17:13:55Z'
NAME = '2026-10-11-h1.json'


def fixture(target=None, issued='2026-10-12T17:12:52Z'):
    return {'id': 'abc', 'issuedAt': issued, 'targetDate': target}


class AnchorTests(unittest.TestCase):
    def test_unknown_target_never_proves_prospective_eligibility(self):
        self.assertEqual(assess(fixture(), STAMP), 'anchored_target_date_unknown')

    def test_target_on_anchor_day_not_proven(self):
        self.assertEqual(assess(fixture('2026-10-12'), STAMP), 'not_proven_before_target_day')

    def test_later_target_is_conservative_day_only(self):
        self.assertEqual(assess(fixture('2026-10-13'), STAMP), 'anchored_before_target_day_only')

    def test_declared_issue_after_publication_is_invalid(self):
        self.assertEqual(assess(fixture('2026-10-13', '2026-10-12T18:00:00Z'), STAMP),
                         'invalid_issued_after_server_anchor')

    def test_bad_target_rejected(self):
        self.assertEqual(assess(fixture('2026-02-30'), STAMP), 'invalid_target_date')

    def test_server_evidence_requires_exact_bytes_and_push(self):
        raw = json.dumps(fixture('2026-10-13')).encode()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / NAME
            path.write_bytes(raw)
            def get(url):
                if url.startswith('/commits?'):
                    return [{'sha': SHA}]
                if url.startswith('/contents/'):
                    return {'encoding': 'base64', 'content': base64.b64encode(raw).decode()}
                if url.startswith('/actions/runs?'):
                    return {'total_count': 2, 'workflow_runs': [
                        {'head_sha': SHA, 'event': 'workflow_dispatch', 'created_at': '2026-10-11T00:00:00Z'},
                        {'head_sha': SHA, 'event': 'push', 'created_at': STAMP, 'id': 123}]}
                raise AssertionError(url)
            result = audit(path, get)
            self.assertEqual(result['status'], 'anchored_before_target_day_only')
            self.assertEqual(result['observedAt'], STAMP)
            self.assertEqual(result['runId'], 123)
            def altered(url):
                if url.startswith('/contents/'):
                    return {'encoding': 'base64', 'content': base64.b64encode(raw+b'\n').decode()}
                return get(url)
            self.assertEqual(audit(path, altered)['status'], 'unanchored')

    def test_no_push_run_means_unanchored(self):
        raw = json.dumps(fixture()).encode()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / NAME
            path.write_bytes(raw)
            def get(url):
                if url.startswith('/commits?'):
                    return [{'sha': SHA}]
                if url.startswith('/contents/'):
                    return {'encoding': 'base64', 'content': base64.b64encode(raw).decode()}
                return {'total_count': 1, 'workflow_runs': [
                    {'head_sha': SHA, 'event': 'workflow_dispatch', 'created_at': STAMP}]}
            self.assertEqual(audit(path, get)['status'], 'unanchored')

    def test_reject_nonreceipt_path(self):
        with self.assertRaises(ValueError):
            audit('/tmp/arbitrary.json', lambda url: None)


if __name__ == '__main__':
    unittest.main()

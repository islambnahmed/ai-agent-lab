"""Adversarial replay tests: hashes alone do not bind CSV content to capture."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from gsc_api_adapter import main as convert_main
from replay_gsc_provenance import replay, main as replay_main
from verify_gsc_export import verify


def capture():
    return {'request': {'startDate': '2026-09-01', 'endDate': '2026-09-02',
                        'dimensions': ['date', 'query', 'page'], 'rowLimit': 10},
            'response': {'rows': [
                {'keys': ['2026-09-01', 'original query', 'https://example.test/a'],
                 'clicks': 1, 'impressions': 20, 'position': 3.0}]}}


class ReplayTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.source = self.root / 'capture.json'
        self.csv = self.root / 'data.csv'
        self.manifest = Path(str(self.csv) + '.manifest.json')
        self.source.write_text(json.dumps(capture()), encoding='utf-8')
        self.assertEqual(convert_main([str(self.source), '--out', str(self.csv)]), 0)

    def test_genuine_replay_passes(self):
        self.assertEqual(replay(self.csv, self.source)['rows_replayed'], 1)
        self.assertEqual(replay_main([str(self.csv), '--capture', str(self.source)]), 0)

    def test_forged_csv_and_updated_hash_pass_old_verifier_but_fail_replay(self):
        altered = self.csv.read_bytes().replace(b'original query', b'fabricated query')
        self.csv.write_bytes(altered)
        m = json.loads(self.manifest.read_text())
        m['output_csv_sha256'] = hashlib.sha256(altered).hexdigest()
        self.manifest.write_text(json.dumps(m))
        # Previous verifier checks two hashes but not the derivation relationship.
        self.assertEqual(verify(self.csv, capture_path=self.source)['status'], 'verified_file_hashes')
        with self.assertRaisesRegex(ValueError, 'deterministic capture replay'):
            replay(self.csv, self.source)

    def test_forged_manifest_metadata_rejected(self):
        m = json.loads(self.manifest.read_text())
        m['pagination_termination'] = 'short_last_page' if m['pagination_termination'] != 'short_last_page' else 'unverified_last_page_full'
        self.manifest.write_text(json.dumps(m))
        verify(self.csv, capture_path=self.source)  # old verifier does not validate semantic metadata
        with self.assertRaisesRegex(ValueError, 'pagination_termination'):
            replay(self.csv, self.source)

    def test_missing_source_fails(self):
        self.source.unlink()
        with self.assertRaises(FileNotFoundError):
            replay(self.csv, self.source)

    def test_modified_capture_fails(self):
        self.source.write_bytes(self.source.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'capture hash mismatch'):
            replay(self.csv, self.source)

    def test_modified_csv_fails(self):
        self.csv.write_bytes(self.csv.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'CSV hash mismatch'):
            replay(self.csv, self.source)

    def test_invalid_capture_rejected(self):
        self.source.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'request metadata'):
            replay(self.csv, self.source)

    def test_cli_nonzero_on_forgery(self):
        self.csv.write_bytes(self.csv.read_bytes() + b'bad')
        self.assertEqual(replay_main([str(self.csv), '--capture', str(self.source)]), 2)


if __name__ == '__main__':
    unittest.main()

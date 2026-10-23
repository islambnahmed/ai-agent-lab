"""Offline regression tests for raw history snapshot retention and auditing."""
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import fetch_data
from snapshot_verify import HISTORY_URL, verify_snapshot


class SnapshotAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.payload = {'metal': 'XAU', 'points': [{'date': '2026-10-21', 'price': 4210}]}
        self.raw = json.dumps(self.payload, separators=(',', ':')).encode('utf-8')
        self.manifest = {'history': {'url': HISTORY_URL, 'status': 'fetched', 'httpStatus': 200,
                                     'rawSha256': hashlib.sha256(self.raw).hexdigest(),
                                     'receivedAt': '2026-10-23T10:00:00Z'}}
        self.write()

    def write(self):
        (self.root / 'history.raw').write_bytes(self.raw)
        (self.root / 'history.json').write_text(json.dumps(self.payload, indent=2), encoding='utf-8')
        (self.root / 'fetch-manifest.json').write_text(json.dumps(self.manifest), encoding='utf-8')

    def test_accepts_exact_raw_bytes_and_equivalent_json(self):
        result = verify_snapshot(self.root)
        self.assertEqual(result['status'], 'verified_local_bytes')
        self.assertEqual(result['rows'], 1)

    def test_rejects_modified_raw_bytes(self):
        (self.root / 'history.raw').write_bytes(self.raw + b' ')
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            verify_snapshot(self.root)

    def test_rejects_modified_parsed_json(self):
        (self.root / 'history.json').write_text(json.dumps({'metal': 'XAU', 'points': []}), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Parsed history differs'):
            verify_snapshot(self.root)

    def test_rejects_missing_raw(self):
        (self.root / 'history.raw').unlink()
        with self.assertRaises(FileNotFoundError):
            verify_snapshot(self.root)

    def test_rejects_failed_fetch(self):
        self.manifest['history']['status'] = 'unavailable'
        self.write()
        with self.assertRaisesRegex(ValueError, 'not a successful'):
            verify_snapshot(self.root)

    def test_rejects_wrong_provider(self):
        self.manifest['history']['url'] = 'https://example.com/market/history'
        self.write()
        with self.assertRaisesRegex(ValueError, 'approved source'):
            verify_snapshot(self.root)

    def test_rejects_invalid_digest(self):
        self.manifest['history']['rawSha256'] = 'abc'
        self.write()
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            verify_snapshot(self.root)

    def test_rejects_unexpected_payload(self):
        self.payload = {'metal': 'AG', 'points': []}
        self.raw = json.dumps(self.payload).encode('utf-8')
        self.manifest['history']['rawSha256'] = hashlib.sha256(self.raw).hexdigest()
        self.write()
        with self.assertRaisesRegex(ValueError, 'unexpected shape'):
            verify_snapshot(self.root)

    def test_rejects_empty_raw(self):
        (self.root / 'history.raw').write_bytes(b'')
        with self.assertRaisesRegex(ValueError, 'size'):
            verify_snapshot(self.root)


class FetchPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def fake_fetch(self, name, url):
        payload = {'metal': 'XAU', 'points': [{'date': '2026-10-21', 'price': 4210}]} if name == 'history' else {'ok': True}
        raw = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        return name, payload, {'url': url, 'status': 'fetched', 'httpStatus': 200,
                               'rawSha256': hashlib.sha256(raw).hexdigest(),
                               'receivedAt': '2026-10-23T10:00:00Z'}, raw

    def test_main_persists_exact_hashed_raw_bytes(self):
        with patch.object(fetch_data, 'ROOT', self.root), patch.object(fetch_data, 'fetch', self.fake_fetch):
            with redirect_stdout(io.StringIO()):
                fetch_data.main()
        self.assertEqual(verify_snapshot(self.root / 'data')['status'], 'verified_local_bytes')

    def test_failed_history_fetch_removes_stale_raw(self):
        data = self.root / 'data'
        data.mkdir()
        (data / 'history.raw').write_bytes(b'stale')
        (data / 'history.json').write_text('"stale"', encoding='utf-8')

        def failing(name, url):
            if name == 'history':
                return name, None, {'url': url, 'status': 'unavailable', 'error': 'offline'}, None
            return self.fake_fetch(name, url)

        with patch.object(fetch_data, 'ROOT', self.root), patch.object(fetch_data, 'fetch', failing):
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                fetch_data.main()
        self.assertFalse((data / 'history.raw').exists())
        self.assertFalse((data / 'history.json').exists())


if __name__ == '__main__':
    unittest.main()

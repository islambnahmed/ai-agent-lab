"""Regression: persisted source snapshot must match manifest rawSha256 exactly."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fetch_data


class Response:
    def __init__(self, body):
        self.body = body
        self.status = 200
        self.headers = {'Access-Control-Allow-Origin': '*'}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, _limit):
        return self.body


class SnapshotBytesTests(unittest.TestCase):
    def run_fetch(self, root, body):
        with patch.object(fetch_data, 'ROOT', root), \
             patch.object(fetch_data, 'URLS', {'history': 'https://example.invalid/history'}), \
             patch.object(fetch_data.urllib.request, 'urlopen', return_value=Response(body)), \
             patch('builtins.print'):
            fetch_data.main()

    def test_persisted_bytes_match_original_hash_even_with_whitespace(self):
        raw = b'{\n  "metal": "XAU", "points": [ {"t": "2026-10-11T00:00:00Z", "price": 4207.98} ]\n}\n'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_fetch(root, raw)
            saved = (root / 'data' / 'history.json').read_bytes()
            manifest = json.loads((root / 'data' / 'fetch-manifest.json').read_text())
            self.assertEqual(saved, raw)
            self.assertEqual(hashlib.sha256(saved).hexdigest(), manifest['history']['rawSha256'])
            self.assertEqual(manifest['history']['status'], 'fetched')

    def test_invalid_json_removes_stale_snapshot_and_records_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'data').mkdir()
            (root / 'data' / 'history.json').write_text('{"old": true}')
            with self.assertRaises(SystemExit) as ctx:
                self.run_fetch(root, b'{"metal":')
            self.assertEqual(ctx.exception.code, 1)
            self.assertFalse((root / 'data' / 'history.json').exists())
            manifest = json.loads((root / 'data' / 'fetch-manifest.json').read_text())
            self.assertEqual(manifest['history']['status'], 'unavailable')
            self.assertNotIn('rawSha256', manifest['history'])


if __name__ == '__main__':
    unittest.main()

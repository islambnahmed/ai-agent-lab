"""Offline regression for byte-exact provider provenance on the peer settlement stack."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import fetch_data


class FetchManifestTests(unittest.TestCase):
    def test_manifest_hashes_exact_saved_history_bytes(self):
        # Intentionally noncanonical whitespace and Unicode; normalization
        # would destroy the byte identity required for raw-source recovery.
        raw = '{\n "metal": "XAU", "grain": "daily", "attribution": "Test café"\n}\n'.encode('utf-8')
        digest = hashlib.sha256(raw).hexdigest()

        def fake_fetch(name, url):
            return name, raw, {'url': url, 'status': 'fetched',
                               'receivedAt': '2025-01-02T12:00:00Z',
                               'rawSha256': digest}

        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(fetch_data, 'ROOT', Path(directory)), \
                 mock.patch.object(fetch_data, 'fetch', side_effect=fake_fetch), \
                 contextlib.redirect_stdout(io.StringIO()):
                fetch_data.main()

            saved = (Path(directory) / 'data/history.json').read_bytes()
            manifest = json.loads(
                (Path(directory) / 'data/fetch-manifest.json').read_text()
            )
            self.assertEqual(saved, raw)
            self.assertEqual(manifest['history']['storedSha256'], digest)
            self.assertEqual(manifest['history']['rawSha256'], digest)
            self.assertIn('café'.encode('utf-8'), saved)


if __name__ == '__main__':
    unittest.main()

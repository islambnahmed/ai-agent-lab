"""Offline regression for stored fetch-manifest provenance (no network)."""
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
        payload = {'metal': 'XAU', 'grain': 'daily',
                   'points': [{'date': '2025-01-01', 'price': 2500}],
                   'attribution': 'Test café'}
        raw_digest = 'a' * 64

        def fake_fetch(name, url):
            return name, payload, {'url': url, 'status': 'fetched',
                                   'receivedAt': '2025-01-02T12:00:00Z',
                                   'rawSha256': raw_digest}

        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(fetch_data, 'ROOT', Path(directory)), \
                 mock.patch.object(fetch_data, 'fetch', side_effect=fake_fetch), \
                 contextlib.redirect_stdout(io.StringIO()):
                fetch_data.main()

            saved = (Path(directory) / 'data/history.json').read_bytes()
            manifest = json.loads(
                (Path(directory) / 'data/fetch-manifest.json').read_text()
            )
            self.assertEqual(
                manifest['history']['storedSha256'],
                hashlib.sha256(saved).hexdigest(),
            )
            self.assertEqual(manifest['history']['rawSha256'], raw_digest)
            # The raw provider digest and normalized stored-byte digest
            # represent different byte streams and must not be conflated.
            self.assertNotEqual(manifest['history']['storedSha256'], raw_digest)
            self.assertIn('café'.encode('utf-8'), saved)


if __name__ == '__main__':
    unittest.main()

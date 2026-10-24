"""Offline regression: fetch manifest must describe exact persisted bytes."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fetch_data


class SnapshotHashTests(unittest.TestCase):
    def test_manifest_binds_saved_json_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = {'metal': 'XAU', 'label': 'أوقية', 'points': [{'date': '2025-01-01', 'price': 2500}]}
            def fake_fetch(name, url):
                return name, payload, {'url': url, 'status': 'fetched',
                                       'rawSha256': hashlib.sha256(b'raw bytes').hexdigest()}
            with patch.object(fetch_data, 'ROOT', Path(directory)), patch.object(fetch_data, 'fetch', side_effect=fake_fetch):
                fetch_data.main()
            manifest = json.loads((Path(directory) / 'data/fetch-manifest.json').read_text())
            for name in fetch_data.URLS:
                saved = (Path(directory) / 'data' / (name + '.json')).read_bytes()
                self.assertEqual(manifest[name]['storedSha256'], hashlib.sha256(saved).hexdigest())
                self.assertEqual(json.loads(saved), payload)
                self.assertNotEqual(manifest[name]['storedSha256'], manifest[name]['rawSha256'])

    def test_failed_fetch_removes_stale_file_without_stored_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / 'data'
            data.mkdir()
            (data / 'spot.json').write_text('stale')
            def fake_fetch(name, url):
                if name == 'spot':
                    return name, None, {'url': url, 'status': 'unavailable'}
                return name, {'ok': True}, {'url': url, 'status': 'fetched',
                                           'rawSha256': hashlib.sha256(b'raw').hexdigest()}
            with patch.object(fetch_data, 'ROOT', Path(directory)), patch.object(fetch_data, 'fetch', side_effect=fake_fetch):
                fetch_data.main()
            self.assertFalse((data / 'spot.json').exists())
            manifest = json.loads((data / 'fetch-manifest.json').read_text())
            self.assertNotIn('storedSha256', manifest['spot'])


if __name__ == '__main__':
    unittest.main()

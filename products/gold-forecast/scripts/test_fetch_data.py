"""Offline regression for fetch manifest/local snapshot binding."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fetch_data


class FakeResponse:
    status = 200
    headers = {'Access-Control-Allow-Origin': '*'}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, _limit):
        # Deliberately unlike json.dumps formatting, to test two hashes.
        return b'{ "metal": "XAU", "note": "\\u03b1" }'


class SnapshotManifestTests(unittest.TestCase):
    def test_manifest_binds_exact_saved_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(fetch_data, 'ROOT', root), \
                 patch.object(fetch_data.urllib.request, 'urlopen', return_value=FakeResponse()):
                fetch_data.main()
            manifest = json.loads((root / 'data/fetch-manifest.json').read_text())
            for name in ('history', 'spot', 'crosscheck'):
                entry = manifest[name]
                stored = (root / 'data' / (name + '.json')).read_bytes()
                self.assertEqual(entry['status'], 'fetched')
                self.assertEqual(entry['storedSha256'], hashlib.sha256(stored).hexdigest())
                self.assertNotEqual(entry['rawSha256'], entry['storedSha256'])
                self.assertEqual(json.loads(stored)['note'], 'α')


if __name__ == '__main__':
    unittest.main()

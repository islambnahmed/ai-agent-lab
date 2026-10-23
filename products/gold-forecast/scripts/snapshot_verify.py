"""Fail-closed local byte-level audit of a Standard Bullion history snapshot.

A matching local digest proves only that the locally saved bytes match the
manifest's recorded digest. It does NOT authenticate provider identity, prove
when data became public, or establish that a price is an exchange close.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

HISTORY_URL = 'https://standardbullion.com/api/v1/market/history?metal=XAU&range=1y'
MAX_RAW_BYTES = 5_000_000


def verify_snapshot(data_dir: Path) -> dict:
    data_dir = Path(data_dir)
    manifest = json.loads((data_dir / 'fetch-manifest.json').read_text(encoding='utf-8'))
    meta = manifest.get('history')
    if not isinstance(meta, dict) or meta.get('status') != 'fetched' or meta.get('httpStatus') != 200:
        raise ValueError('History manifest is not a successful HTTP 200 fetch')
    if meta.get('url') != HISTORY_URL:
        raise ValueError('History endpoint does not match approved source')
    expected = meta.get('rawSha256')
    if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected):
        raise ValueError('Missing or invalid raw SHA-256')
    raw = (data_dir / 'history.raw').read_bytes()
    if not raw or len(raw) > MAX_RAW_BYTES:
        raise ValueError('Invalid raw response size')
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise ValueError('Raw response digest mismatch')
    original = json.loads(raw)
    saved = json.loads((data_dir / 'history.json').read_text(encoding='utf-8'))
    if original != saved:
        raise ValueError('Parsed history differs from original raw response')
    if not isinstance(original, dict) or original.get('metal') != 'XAU' or not isinstance(original.get('points'), list):
        raise ValueError('History payload has unexpected shape')
    return {
        'status': 'verified_local_bytes',
        'sourceUrl': HISTORY_URL,
        'rawSha256': actual,
        'bytes': len(raw),
        'rows': len(original['points']),
        'receivedAt': meta.get('receivedAt'),
        'caveat': 'Local byte equality only; provider authenticity and publication timing are unverified',
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parents[1] / 'data')
    args = parser.parse_args()
    print(json.dumps(verify_snapshot(args.data_dir), indent=2))


if __name__ == '__main__':
    main()

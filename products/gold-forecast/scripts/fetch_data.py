"""Fetch provenance-tagged snapshots for local research, without publishing feeds.

python products/gold-forecast/scripts/fetch_data.py
Use 1y: the provider's 5y request was decimated, and dated-window requests
returned observations outside the requested window in the 2026-10-12 probe.
A successful HTTP request alone is not evidence of the requested coverage.
"""
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
URLS = {
    'history': 'https://standardbullion.com/api/v1/market/history?metal=XAU&range=1y',
    'spot': 'https://standardbullion.com/spot-prices.json',
    'crosscheck': 'https://api.gold-api.com/price/XAU',
}

def timestamp():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

def atomic_write_text(dest, text):
    """Replace a complete file; an interrupted write must not truncate the cache."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=dest.parent,
                                         prefix='.' + dest.name + '.', delete=False) as out:
            tmp = Path(out.name)
            out.write(text)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, dest)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)

def fetch(name, url):
    requested_at = timestamp()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GoldLab/2.0 research'})
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read(5_000_001)
            if len(raw) > 5_000_000:
                raise ValueError('Provider response too large')
            payload = json.loads(raw)
            meta = {'url': url, 'requestedAt': requested_at, 'receivedAt': timestamp(),
                    'httpStatus': response.status, 'cors': response.headers.get('Access-Control-Allow-Origin'),
                    'rawSha256': hashlib.sha256(raw).hexdigest(), 'status': 'fetched'}
            return name, payload, meta
    except Exception as exc:
        return name, None, {'url': url, 'requestedAt': requested_at, 'status': 'unavailable', 'error': str(exc)}

def main():
    ROOT.joinpath('data').mkdir(exist_ok=True)
    result = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for future in [pool.submit(fetch, name, url) for name, url in URLS.items()]:
            name, payload, meta = future.result()
            result[name] = meta
            dest = ROOT / 'data' / (name + '.json')
            if payload is not None:
                serialized = json.dumps(payload, ensure_ascii=False)
                atomic_write_text(dest, serialized)
                meta['snapshotSha256'] = hashlib.sha256(serialized.encode('utf-8')).hexdigest()
            else:
                # Preserve the last good bytes for recovery. Consumers must
                # reject this snapshot because the new manifest says unavailable.
                meta['cachedSnapshotPreserved'] = dest.exists()
    result['coveragePolicy'] = {
        'requestedRange': '1y', 'longHistoryStatus': 'blocked_by_provider_contract',
        'reason': '5y downsampling; dated queries did not respect requested bounds in 2026-10-12 probe',
        'historicalVintage': 'current snapshot; no claim of historical release-time availability',
    }
    atomic_write_text(ROOT / 'data/fetch-manifest.json', json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    if result['history']['status'] != 'fetched':
        raise SystemExit(1)

if __name__ == '__main__':
    main()

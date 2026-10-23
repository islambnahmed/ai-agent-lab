"""Fetch provenance-tagged snapshots for local research, without publishing feeds.

python products/gold-forecast/scripts/fetch_data.py
Use 1y: the provider's 5y request was decimated, and dated-window requests
returned observations outside the requested window in the 2026-10-12 probe.
A successful HTTP request alone is not evidence of the requested coverage.

Exact raw history response bytes are kept in ignored data/history.raw so the
manifest's rawSha256 can be audited later. This is local integrity evidence,
not independent proof of provider publication time or authenticity.
"""
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
URLS = {
    'history': 'https://standardbullion.com/api/v1/market/history?metal=XAU&range=1y',
    'spot': 'https://standardbullion.com/spot-prices.json',
    'crosscheck': 'https://api.gold-api.com/price/XAU',
}

def timestamp():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

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
            return name, payload, meta, raw
    except Exception as exc:
        return name, None, {'url': url, 'requestedAt': requested_at, 'status': 'unavailable', 'error': str(exc)}, None

def main():
    ROOT.joinpath('data').mkdir(exist_ok=True)
    result = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for future in [pool.submit(fetch, name, url) for name, url in URLS.items()]:
            name, payload, meta, raw = future.result()
            result[name] = meta
            dest = ROOT / 'data' / (name + '.json')
            if payload is not None:
                if name == 'history':
                    # Preserve exact hashed bytes, not re-serialized JSON.
                    (ROOT / 'data/history.raw').write_bytes(raw)
                dest.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
            else:
                dest.unlink(missing_ok=True)  # never pass an old failed-fetch snapshot
                if name == 'history':
                    (ROOT / 'data/history.raw').unlink(missing_ok=True)
    result['coveragePolicy'] = {
        'requestedRange': '1y', 'longHistoryStatus': 'blocked_by_provider_contract',
        'reason': '5y downsampling; dated queries did not respect requested bounds in 2026-10-12 probe',
        'historicalVintage': 'current snapshot; no claim of historical release-time availability',
    }
    ROOT.joinpath('data/fetch-manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    if result['history']['status'] != 'fetched':
        raise SystemExit(1)

if __name__ == '__main__':
    main()

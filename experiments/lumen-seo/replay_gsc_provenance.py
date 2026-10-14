#!/usr/bin/env python3
"""Offline semantic replay of a saved GSC capture against its CSV and manifest.

Hashes only establish file consistency, not provenance. Replay additionally checks
that the saved capture *actually generates* the claimed CSV and metadata.
It does not authenticate Google or establish full Search Analytics coverage.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

from gsc_api_adapter import COLUMNS, MAX_INPUT_BYTES, convert

META_FIELDS = (
    'schema_version', 'input_format', 'request_dimensions', 'search_type',
    'date_range', 'pagination_pages', 'rows_received', 'rows_excluded_incomplete',
    'rows_written', 'first_incomplete_date', 'pagination_termination',
)


def replay(csv_path, capture_path, manifest_path=None):
    csv_path = Path(csv_path)
    capture_path = Path(capture_path)
    manifest_path = Path(manifest_path) if manifest_path else Path(str(csv_path) + '.manifest.json')
    raw_capture = capture_path.read_bytes()
    if len(raw_capture) > MAX_INPUT_BYTES:
        raise ValueError('capture exceeds adapter input limit')
    capture = json.loads(raw_capture.decode('utf-8-sig'))
    rows, expected = convert(capture)
    actual_manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if not isinstance(actual_manifest, dict):
        raise ValueError('manifest must be a JSON object')
    actual_csv = csv_path.read_bytes()
    if actual_manifest.get('input_sha256') != hashlib.sha256(raw_capture).hexdigest():
        raise ValueError('capture hash mismatch')
    if actual_manifest.get('output_csv_sha256') != hashlib.sha256(actual_csv).hexdigest():
        raise ValueError('CSV hash mismatch')
    for field in META_FIELDS:
        if actual_manifest.get(field) != expected[field]:
            raise ValueError(f'manifest {field} differs from replay')
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer)
    writer.writerow(COLUMNS)
    for day, query, page, clicks, impressions, position in rows:
        writer.writerow((day.isoformat(), query, page, clicks, impressions, position))
    if actual_csv != buffer.getvalue().encode('utf-8'):
        raise ValueError('CSV bytes differ from deterministic capture replay')
    return {'status': 'capture_replay_consistent', 'rows_replayed': len(rows),
            'csv_sha256': hashlib.sha256(actual_csv).hexdigest(),
            'limitations': [
                'The capture is user-supplied and is not authenticated as a Google response.',
                'The Search Analytics API can omit rows; replay does not prove coverage.',
                'A coordinated rewrite of capture, CSV and manifest can still pass.'
            ]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_path')
    parser.add_argument('--capture', required=True)
    parser.add_argument('--manifest')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(replay(args.csv_path, args.capture, args.manifest), indent=2))
        return 0
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({'status': 'replay_failed', 'error': str(exc)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())

"""Offline C333 study-lock wrapper: reject dataset/protocol drift before evaluation.

Use only inside authorized lab. Reviewer sheets and real audit data are private;
this tool never sends data over a network. SHA-256 is an integrity fingerprint,
not a signature, independent timestamp, or proof of human review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'c333'))
from time_budget_study import make_packets, evaluate_time  # noqa: E402
from ranking_benchmark import candidates, load_json  # noqa: E402

SCHEMA = 'worker-a-study-lock/v1'
CODE_PATHS = {
    'ranking_benchmark': ROOT / 'c332' / 'ranking_benchmark.py',
    'time_budget_study': ROOT / 'c333' / 'time_budget_study.py',
}
PACKET_KEYS = {'reviewer', 'synthetic_or_user_supplied', 'instructions', 'items'}
ITEM_KEYS = {'url', 'matched_rule', 'label', 'seconds', 'evidence_note'}
SHA = re.compile(r'^[0-9a-f]{64}$')


def digest(value: object) -> str:
    """Canonical JSON fingerprint, insensitive to JSON formatting or key order."""
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def code_digests() -> dict[str, str]:
    return {name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in CODE_PATHS.items()}


def valid_budgets(budgets: list[int]) -> None:
    if (not isinstance(budgets, (list, tuple)) or not budgets or
            len(set(map(str, budgets))) != len(budgets) or
            any(type(b) is not int or b <= 0 for b in budgets)):
        raise ValueError('budgets must be unique positive integer reviewer-seconds')


def make_study(report: dict, seed: int, budgets: list[int]) -> tuple[dict, dict, dict]:
    valid_budgets(budgets)
    candidates(report)  # Fail early on duplicate/malformed inventory.
    a, b = make_packets(report, seed)
    manifest = {
        'schema': SCHEMA,
        'audit_sha256': digest(report),
        'code_sha256': code_digests(),
        'seed': seed,
        'budget_seconds': list(budgets),
        'candidate_count': len(a['items']),
        'evaluation': 'C333 strict-prefix dual-reviewer-seconds; retrospective only',
        'review_provenance': 'reviewer-supplied, not independently verified',
        'privacy': 'No client URLs, evidence notes, or review sheets belong in a public repo.',
    }
    return manifest, a, b


def _check_packet(actual: dict, expected: dict) -> None:
    if not isinstance(actual, dict) or set(actual) != PACKET_KEYS:
        raise ValueError('review packet has unexpected top-level fields')
    for key in ('reviewer', 'synthetic_or_user_supplied', 'instructions'):
        if actual[key] != expected[key]:
            raise ValueError(f'reviewer packet immutable field changed: {key}')
    if not isinstance(actual['items'], list) or len(actual['items']) != len(expected['items']):
        raise ValueError('review packet candidate count changed')
    for row, baseline in zip(actual['items'], expected['items']):
        if not isinstance(row, dict) or set(row) != ITEM_KEYS:
            raise ValueError('review packet has unexpected item fields')
        if row['url'] != baseline['url'] or row['matched_rule'] != baseline['matched_rule']:
            raise ValueError('review packet URL order or matched rule changed')


def verify_and_evaluate(manifest: dict, report: dict, a: dict, b: dict,
                        expected_manifest_sha256: str, budgets: list[int] | None = None) -> dict:
    if not isinstance(manifest, dict) or set(manifest) != {
        'schema', 'audit_sha256', 'code_sha256', 'seed', 'budget_seconds',
        'candidate_count', 'evaluation', 'review_provenance', 'privacy'
    } or manifest['schema'] != SCHEMA:
        raise ValueError('unknown or invalid study manifest')
    if not isinstance(expected_manifest_sha256, str) or not SHA.fullmatch(expected_manifest_sha256):
        raise ValueError('a previously pinned 64-character study SHA-256 is required')
    if digest(manifest) != expected_manifest_sha256:
        raise ValueError('study manifest changed relative to pinned fingerprint')
    if type(manifest['seed']) is not int or type(manifest['candidate_count']) is not int:
        raise ValueError('manifest seed/count invalid')
    locked_budgets = manifest['budget_seconds']
    valid_budgets(locked_budgets)
    if budgets is not None and list(budgets) != locked_budgets:
        raise ValueError('evaluation budgets differ from preregistered study')
    if not isinstance(manifest['audit_sha256'], str) or not SHA.fullmatch(manifest['audit_sha256']):
        raise ValueError('invalid audit digest')
    if manifest['audit_sha256'] != digest(report):
        raise ValueError('audit changed after study preparation')
    if manifest['code_sha256'] != code_digests():
        raise ValueError('ranking or evaluation code changed after study preparation')
    expected_manifest, expected_a, expected_b = make_study(report, manifest['seed'], locked_budgets)
    if manifest != expected_manifest:
        raise ValueError('study manifest contents differ from locked protocol')
    _check_packet(a, expected_a)
    _check_packet(b, expected_b)
    result = evaluate_time(report, a, b, locked_budgets)
    result['study_lock'] = {
        'schema': SCHEMA,
        'manifest_sha256': digest(manifest),
        'audit_sha256': manifest['audit_sha256'],
        'code_sha256': manifest['code_sha256'],
        'caveat': ('A manifest can be replaced along with its inputs; independent immutable '
                   'commit or external preregistration of the expected fingerprint is required. '
                   'Human labels and durations are not independently authenticated.'),
    }
    return result


def write_json_new(path: Path, obj: object) -> None:
    """Exclusive creation; never overwrite a review sheet or result."""
    with path.open('x', encoding='utf-8') as stream:
        json.dump(obj, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--audit', type=Path, required=True)
    p.add_argument('--seed', type=int, required=True)
    p.add_argument('--budget-seconds', type=int, nargs='+', required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    e = sub.add_parser('evaluate')
    e.add_argument('--audit', type=Path, required=True)
    e.add_argument('--study-dir', type=Path, required=True)
    e.add_argument('--output', type=Path, required=True)
    e.add_argument('--expected-study-sha256', required=True,
                   help='study SHA-256 from prepare, pinned independently before review')
    args = parser.parse_args(argv)
    try:
        report = load_json(args.audit)
        if args.command == 'prepare':
            manifest, a, b = make_study(report, args.seed, args.budget_seconds)
            if args.output_dir.exists() or args.output_dir.is_symlink():
                raise ValueError('study output directory exists; refusing overwrite')
            # Stage locally, then publish a complete study folder with one rename.
            args.output_dir.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='.study-stage-', dir=args.output_dir.parent) as stage:
                tmp = Path(stage)
                write_json_new(tmp / 'manifest.json', manifest)
                write_json_new(tmp / 'reviewer_a.json', a)
                write_json_new(tmp / 'reviewer_b.json', b)
                tmp.rename(args.output_dir)
            print(json.dumps({'study_sha256': digest(manifest), 'candidates': manifest['candidate_count']}))
        else:
            if args.output.exists():
                raise ValueError('evaluation output exists; refusing overwrite')
            study = args.study_dir
            result = verify_and_evaluate(load_json(study / 'manifest.json'), report,
                                         load_json(study / 'reviewer_a.json'),
                                         load_json(study / 'reviewer_b.json'),
                                         args.expected_study_sha256)
            write_json_new(args.output, result)
            print(json.dumps({'study_sha256': result['study_lock']['manifest_sha256'],
                              'candidates': result['candidate_count']}))
    except (ValueError, OSError, TypeError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()

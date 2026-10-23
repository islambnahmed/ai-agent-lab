"""Offline, blinded two-reviewer timing study for C332 SEO queues.

This is a retrospective *what-if* comparison, NOT evidence of real-world time savings.
No HTTP, telemetry, credentials, or external data are used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'c332'))
from ranking_benchmark import candidates, rankings, agreement, load_json, LABELS  # noqa: E402

MAX_ITEMS = 50000
MAX_NOTE = 2000


def make_packets(report: dict, seed: int) -> tuple[dict, dict]:
    """Hide ranking fields and existing intent labels from the two independent raters."""
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rows = candidates(report)
    source = {r['url']: r for r in report['rows'] if r.get('status') == 'disallowed'}
    packets = []
    for index, reviewer in enumerate(('a', 'b')):
        order = list(rows)
        random.Random(f'{seed}:{index}').shuffle(order)
        packets.append({
            'reviewer': reviewer,
            'synthetic_or_user_supplied': 'reviewer-provided; not independently verified',
            'instructions': ('Use independent evidence of page purpose and intended crawl policy. '
                             'Unknown is valid; do not infer intent from clicks or rank. '
                             'Record measured elapsed seconds, not an estimate. '
                             'Never publish client URLs or private evidence.'),
            'items': [{
                'url': r['url'],
                'matched_rule': source[r['url']].get('matched_rule', ''),
                'label': 'unknown', 'seconds': None, 'evidence_note': ''
            } for r in order]
        })
    return packets[0], packets[1]


def _parse_sheet(sheet: dict, reviewer: str, urls: set[str]) -> dict:
    if not isinstance(sheet, dict) or sheet.get('reviewer') != reviewer or not isinstance(sheet.get('items'), list):
        raise ValueError(f'reviewer {reviewer} sheet invalid')
    if len(sheet['items']) != len(urls) or len(sheet['items']) > MAX_ITEMS:
        raise ValueError(f'reviewer {reviewer} must cover every candidate exactly once')
    result = {}
    for item in sheet['items']:
        if not isinstance(item, dict) or not isinstance(item.get('url'), str):
            raise ValueError('invalid review item')
        url = item['url']
        if url not in urls or url in result:
            raise ValueError('review sheet contains duplicate or unexpected URL')
        label = item.get('label')
        seconds = item.get('seconds')
        note = item.get('evidence_note')
        if not isinstance(label, str) or label not in LABELS:
            raise ValueError('invalid review label')
        if type(seconds) is not int or not 1 <= seconds <= 3600:
            raise ValueError('seconds must be a measured integer in 1..3600 for each review')
        if not isinstance(note, str) or len(note) > MAX_NOTE:
            raise ValueError('evidence_note must be text <=2000 characters')
        if label != 'unknown' and not note.strip():
            raise ValueError('known intent requires an evidence_note')
        result[url] = {'label': label, 'seconds': seconds, 'evidence_note': note}
    return result


def evaluate_time(report: dict, a_sheet: dict, b_sheet: dict, budgets: list[int]) -> dict:
    rows = candidates(report)
    urls = {r['url'] for r in rows}
    if not isinstance(budgets, (list, tuple)) or not budgets or any(type(b) is not int or b <= 0 for b in budgets):
        raise ValueError('budgets must be positive integer seconds')
    a = _parse_sheet(a_sheet, 'a', urls)
    b = _parse_sheet(b_sheet, 'b', urls)
    labels = {u: {'rater_a': a[u]['label'], 'rater_b': b[u]['label']} for u in urls}
    costs = {u: a[u]['seconds'] + b[u]['seconds'] for u in urls}
    output = {}
    for method, order in rankings(rows).items():
        scores = {}
        for budget in budgets:
            selected, spent = [], 0
            for u in order:
                if spent + costs[u] > budget:
                    break  # strict prefix; never cherry-pick cheap later items
                selected.append(u)
                spent += costs[u]
            positive = sum(labels[u]['rater_a'] == labels[u]['rater_b'] == 'accidental' for u in selected)
            negative = sum(labels[u]['rater_a'] == labels[u]['rater_b'] == 'intentional' for u in selected)
            scores[str(budget)] = {
                'reviewed': len(selected), 'spent_reviewer_seconds': spent,
                'confirmed_accidental': positive, 'confirmed_intentional': negative,
                'unresolved': len(selected) - positive - negative,
                'confirmed_per_reviewer_hour': round(positive * 3600 / spent, 6) if spent else None,
            }
        output[method] = {'at_seconds': scores}
    return {
        'candidate_count': len(rows), 'reviewer_count': 2, 'all_candidates_dual_reviewed': True,
        'agreement': agreement(labels), 'rankings': output,
        'limitations': ('All durations and labels are reviewer-supplied and unverified. '
                        'This is a retrospective strict-prefix simulation on a fixed reviewed set; '
                        'review time may depend on order, fatigue, expertise, or information availability. '
                        'It is not a randomized field trial, a traffic recovery estimate, or a causal productivity claim.')
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare', help='create two independently shuffled, label-blind review sheets')
    prep.add_argument('--audit', type=Path, required=True)
    prep.add_argument('--seed', type=int, required=True)
    prep.add_argument('--output-dir', type=Path, required=True)
    ev = sub.add_parser('evaluate', help='evaluate completed sheets under total reviewer-second budgets')
    ev.add_argument('--audit', type=Path, required=True)
    ev.add_argument('--reviewer-a', type=Path, required=True)
    ev.add_argument('--reviewer-b', type=Path, required=True)
    ev.add_argument('--budget-seconds', type=int, nargs='+', required=True)
    ev.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = load_json(args.audit)
        if args.command == 'prepare':
            a, b = make_packets(report, args.seed)
            args.output_dir.mkdir(parents=True, exist_ok=True)
            targets = {r: args.output_dir / f'reviewer_{r}.json' for r in ('a', 'b')}
            for target in targets.values():
                if target.exists():
                    raise ValueError(f'will not overwrite existing sheet: {target}')
            for reviewer, packet in (('a', a), ('b', b)):
                targets[reviewer].write_text(json.dumps(packet, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            print('Prepared two blank, blinded review sheets; no labels or measured times supplied.')
        else:
            result = evaluate_time(report, load_json(args.reviewer_a), load_json(args.reviewer_b), args.budget_seconds)
            args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            print(json.dumps({'candidate_count': result['candidate_count'], 'agreement': result['agreement']}))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()

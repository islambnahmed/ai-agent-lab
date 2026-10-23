"""Offline, label-blind robots.txt review-queue ranking benchmark.

Evaluates *human-review ordering* only. No network requests or SEO outcome claims.
Audit JSON comes from C330/C331; labels live in a separate, synthetic or analyst-supplied file.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
import json
from pathlib import Path

MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 50000
LABELS = {'accidental', 'intentional', 'unknown'}


def load_json(path: Path):
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError('JSON input exceeds 10 MiB')
    try:
        return json.loads(raw.decode('utf-8'))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('JSON input must be valid UTF-8 JSON') from exc


def candidates(report: dict) -> list[dict]:
    """Only definite disallowed rows are assessed for intent; unknown != blocked."""
    if not isinstance(report, dict) or not isinstance(report.get('rows'), list):
        raise ValueError('audit report requires rows array')
    rows = report['rows']
    if len(rows) > MAX_ROWS:
        raise ValueError('too many rows')
    found, output = set(), []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('url'), str) or not row['url']:
            raise ValueError('row must have nonempty URL')
        if row['url'] in found:
            raise ValueError('duplicate URL in report; resolve before benchmarking')
        found.add(row['url'])
        if row.get('status') != 'disallowed':
            continue
        clicks, segment = row.get('organic_clicks_30d'), row.get('segment')
        if type(clicks) is not int or not 0 <= clicks <= 10**9:
            raise ValueError('disallowed row requires valid nonnegative integer clicks')
        if not isinstance(segment, str) or not 1 <= len(segment) <= 80:
            raise ValueError('disallowed row requires nonempty segment <=80 chars')
        # Whitelist fields: rater labels in the audit input cannot leak into ranking.
        output.append({'url': row['url'], 'clicks': clicks, 'segment': segment})
    return output


def rankings(rows: list[dict]) -> dict[str, list[str]]:
    ordered = sorted(rows, key=lambda r: (-r['clicks'], r['url']))
    by_segment = defaultdict(deque)
    segment_max = {}
    for row in ordered:
        by_segment[row['segment']].append(row['url'])
        segment_max.setdefault(row['segment'], row['clicks'])
    # Fixed, data-only segment order; round-robin prevents a single segment
    # from consuming every early review slot. No ground-truth labels are read.
    segment_order = sorted(by_segment, key=lambda s: (-segment_max[s], s))
    balanced = []
    while any(by_segment.values()):
        for segment in segment_order:
            if by_segment[segment]:
                balanced.append(by_segment[segment].popleft())
    return {'clicks_desc': [r['url'] for r in ordered], 'segment_round_robin': balanced}


def _check_labels(labels: dict, candidate_urls: set[str]):
    if not isinstance(labels, dict):
        raise ValueError('labels must be a URL-to-two-raters object')
    for url, entry in labels.items():
        if url not in candidate_urls:
            raise ValueError(f'label URL not in disallowed candidates: {url}')
        if not isinstance(entry, dict) or set(entry) != {'rater_a', 'rater_b'}:
            raise ValueError('each label requires exactly rater_a and rater_b')
        if entry['rater_a'] not in LABELS or entry['rater_b'] not in LABELS:
            raise ValueError('invalid human label')


def agreement(labels: dict) -> dict:
    dual = [v for v in labels.values() if v['rater_a'] != 'unknown' and v['rater_b'] != 'unknown']
    n = len(dual)
    if not n:
        return {'dual_known': 0, 'agreement_rate': None, 'cohen_kappa': None}
    agree = sum(v['rater_a'] == v['rater_b'] for v in dual)
    p_o = agree / n
    a = Counter(v['rater_a'] for v in dual)
    b = Counter(v['rater_b'] for v in dual)
    p_e = sum(a[c] * b[c] for c in ('accidental', 'intentional')) / n**2
    kappa = (p_o - p_e) / (1 - p_e) if p_e < 1 else None
    return {'dual_known': n, 'agreement_rate': round(p_o, 6),
            'cohen_kappa': round(kappa, 6) if kappa is not None else None}


def evaluate(report: dict, labels: dict, ks=(3, 5, 10)) -> dict:
    rows = candidates(report)
    urls = {r['url'] for r in rows}
    _check_labels(labels, urls)
    if not isinstance(ks, (list, tuple)) or not ks or any(type(k) is not int or k < 1 for k in ks):
        raise ValueError('ks must be positive integers')
    orders = rankings(rows)
    comparisons = {}
    for method, order in orders.items():
        scores = {}
        for k in ks:
            reviewed = order[:k]
            positive = negative = 0
            for url in reviewed:
                v = labels.get(url, {'rater_a': 'unknown', 'rater_b': 'unknown'})
                if v['rater_a'] == v['rater_b'] == 'accidental':
                    positive += 1
                elif v['rater_a'] == v['rater_b'] == 'intentional':
                    negative += 1
            unresolved = len(reviewed) - positive - negative
            denom = len(reviewed)
            scores[str(k)] = {'reviewed': denom, 'confirmed_accidental': positive,
                              'confirmed_intentional': negative, 'unresolved': unresolved,
                              'precision_lower_bound': round(positive / denom, 6) if denom else None,
                              'precision_upper_bound': round((positive + unresolved) / denom, 6) if denom else None}
        comparisons[method] = {'top_urls': order[:max(ks)], 'at_k': scores}
    consensus = Counter()
    for url in urls:
        v = labels.get(url, {'rater_a': 'unknown', 'rater_b': 'unknown'})
        if v['rater_a'] == v['rater_b'] == 'accidental':
            consensus['confirmed_accidental'] += 1
        elif v['rater_a'] == v['rater_b'] == 'intentional':
            consensus['confirmed_intentional'] += 1
        else:
            consensus['unresolved'] += 1
    return {'candidate_count': len(rows), 'labels_provided': len(labels),
            'consensus': dict(consensus), 'agreement': agreement(labels),
            'rankings': comparisons,
            'interpretation': ('Offline review-order benchmark only. Labels are separate from ranking inputs; '
                               'unlabeled, unknown and disagreeing raters remain unresolved. Precision bounds '
                               'are descriptive, not estimates of recall, ranking lift, Googlebot behavior, '
                               'indexability, or traffic recovered. Synthetic fixtures cannot validate field performance.')}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--audit', type=Path, required=True)
    ap.add_argument('--labels', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--k', type=int, nargs='+', default=[3, 5, 10])
    args = ap.parse_args(argv)
    try:
        result = evaluate(load_json(args.audit), load_json(args.labels), args.k)
    except (ValueError, OSError) as exc:
        ap.error(str(exc))
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'candidate_count': result['candidate_count'], 'agreement': result['agreement']}, sort_keys=True))


if __name__ == '__main__':
    main()

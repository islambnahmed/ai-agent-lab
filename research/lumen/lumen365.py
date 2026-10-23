"""Lumen 365: frozen synthetic membership + independent outcome-oracle audit.

This demonstrates Git-history ordering, not external independent attestation.
A valid membership hash never authenticates aggregate count values.
"""
import hashlib
import itertools
import json
from pathlib import Path

PRECOMMIT_SHA256 = 'd67e387f31080738455fa58fc059601c283a427d279661d1d3d6c18178f5f9a4'
PRECOMMIT_COMMIT = '3f132eb95c88e97d58763f05659ad016dbc4bbf4'


def audit(manifest_bytes, counts, *, oracle=None, max_error_rate=0.4):
    """Fail closed unless BOTH precommitted membership and lab labels agree.

    All outcomes are binary, all group reports are exact counts. Enumerating
    feasible outcomes is practical only for small fixtures (<=16 cases).
    """
    result = {'decision': 'abstain', 'membership_verified': False,
              'aggregate_values_verified': False,
              'provenance_scope': 'local_sha256_and_git_history_order_only'}
    if hashlib.sha256(manifest_bytes).hexdigest() != PRECOMMIT_SHA256:
        return result | {'reason': 'membership_digest_mismatch'}
    try:
        frame = json.loads(manifest_bytes)
        ids, groups = frame['case_ids'], frame['groups']
        assert frame['fixture_id'] == 'lumen365_balanced_overlap_v1'
        assert isinstance(ids, list) and 0 < len(ids) <= 16
        assert len(ids) == len(set(ids))
        assert isinstance(groups, dict) and len(groups) > 0
        assert all(len(m) == len(set(m)) and len(m) > 0 and set(m) <= set(ids)
                   for m in groups.values())
        assert type(max_error_rate) in (float, int) and 0 <= max_error_rate <= 1
        assert isinstance(counts, dict) and set(counts) == set(groups)
        assert all(type(counts[g]) is int and 0 <= counts[g] <= len(groups[g]) for g in groups)
    except (ValueError, KeyError, AssertionError, TypeError):
        return result | {'reason': 'invalid_fixture_or_counts'}
    result['membership_verified'] = True
    feasible = []
    for bits in itertools.product((0, 1), repeat=len(ids)):
        labels = dict(zip(ids, bits))
        if all(sum(labels[c] for c in members) == counts[g]
               for g, members in groups.items()):
            feasible.append(sum(bits))
    if not feasible:
        return result | {'reason': 'infeasible_aggregate_constraints'}
    lo, hi = min(feasible), max(feasible)
    result.update({'min_errors': lo, 'max_errors': hi,
                   'lower_rate': lo / len(ids), 'upper_rate': hi / len(ids),
                   'feasible_assignments': len(feasible),
                   'conditional_decision': ('accept' if hi / len(ids) <= max_error_rate
                                            else 'reject' if lo / len(ids) > max_error_rate
                                            else 'abstain')})
    # Distinct closed-form oracle: each case appears in exactly two groups.
    degrees = {c: sum(c in members for members in groups.values()) for c in ids}
    if set(degrees.values()) == {2}:
        total = sum(counts.values())
        if total % 2 or not lo == hi == total // 2:
            return result | {'reason': 'double_count_invariant_failed'}
        result['double_count_invariant'] = total // 2
    if oracle is None:
        return result | {'reason': 'aggregate_values_not_independently_checked'}
    if not isinstance(oracle, dict) or set(oracle) != set(ids) or any(type(v) is not int or v not in (0, 1) for v in oracle.values()):
        return result | {'reason': 'invalid_oracle'}
    expected = {g: sum(oracle[c] for c in members) for g, members in groups.items()}
    if counts != expected:
        return result | {'reason': 'aggregate_oracle_mismatch', 'mismatched_groups':
                         sorted(g for g in groups if counts[g] != expected[g])}
    result['aggregate_values_verified'] = True
    result['decision'] = result['conditional_decision']
    result['reason'] = 'checked_against_synthetic_lab_oracle_not_production'
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest', type=Path)
    parser.add_argument('observations', type=Path)
    parser.add_argument('--oracle', type=Path)
    args = parser.parse_args()
    counts = json.loads(args.observations.read_text())['counts']
    oracle = json.loads(args.oracle.read_text())['labels'] if args.oracle else None
    result = audit(args.manifest.read_bytes(), counts, oracle=oracle)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['decision'] in ('accept', 'reject') else 2


if __name__ == '__main__':
    raise SystemExit(main())

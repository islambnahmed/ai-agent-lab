"""Lumen 364: fail-closed audit gate for unknown group cardinality.

This is a conditional, deterministic identification analysis, NOT a confidence
interval or independent attestation of provenance. Requires lumen363.py.
"""
import argparse
import json
import math
from pathlib import Path
from lumen363 import (Report, sensitivity_bounds, InvalidEvidence,
                      InfeasibleEvidence, SearchLimit)


def _nonneg_int(x, label):
    if type(x) is not int or x < 0:
        raise InvalidEvidence(f'{label} must be a nonnegative integer')
    return x


def audit(payload):
    """Return auditable sensitivity decisions; never accept if any tested model is undecidable.

    The tested model family is itself a user-supplied assumption. A result of
    'accept_within_assumptions' is not a real-world safety certification.
    """
    if not isinstance(payload, dict):
        raise InvalidEvidence('input must be an object')
    threshold = payload.get('max_error_rate')
    if type(threshold) not in (float, int) or not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise InvalidEvidence('max_error_rate must be finite in [0,1]')
    entities = payload.get('entities')
    raw = payload.get('reports')
    uncertain = payload.get('uncertain_groups', [])
    if not isinstance(entities, list) or not isinstance(raw, list) or not isinstance(uncertain, list):
        raise InvalidEvidence('entities, reports, uncertain_groups must be arrays')
    if not entities or len(entities) > 24 or any(not isinstance(e, str) or not e for e in entities) or len(set(entities)) != len(entities):
        raise InvalidEvidence('entities must contain 1-24 unique nonempty string IDs')
    if any(not isinstance(name, str) for name in uncertain):
        raise InvalidEvidence('uncertain group names must be strings')
    reports = []
    for item in raw:
        if not isinstance(item, dict) or set(item) != {'name', 'members', 'kind', 'value'} or not isinstance(item['members'], list):
            raise InvalidEvidence('each report requires name, members array, kind, value')
        if not isinstance(item['name'], str) or not item['name'] or any(not isinstance(m, str) for m in item['members']):
            raise InvalidEvidence('report names and member IDs must be strings')
        reports.append(Report(item['name'], tuple(item['members']), item['kind'], item['value']))
    radius = _nonneg_int(payload.get('max_radius', 0), 'max_radius')
    if radius > len(entities):
        raise InvalidEvidence('max_radius cannot exceed entity count')
    b = _nonneg_int(payload.get('max_membership_changes', 0), 'max_membership_changes')
    k = _nonneg_int(payload.get('max_corrupt_values', 0), 'max_corrupt_values')
    max_options = _nonneg_int(payload.get('max_options', 100_000), 'max_options')
    max_work = _nonneg_int(payload.get('max_work', 3_000_000), 'max_work')
    if not max_options or not max_work:
        raise InvalidEvidence('resource caps must be positive')
    # Explicitly test both cardinality assumptions at every radius, not only
    # the nominal/maximum radius, to reveal sensitivity rather than conceal it.
    rows = []
    for d in range(radius + 1):
        for preserve in (True, False):
            try:
                result = sensitivity_bounds(tuple(entities), reports, uncertain,
                    radius=d, max_membership_changes=b, max_corrupt_values=k,
                    preserve_group_size=preserve,
                    max_options=max_options, max_work=max_work)
                lower, upper = result['lower_rate'], result['upper_rate']
                # Equality with maximum permitted error is acceptable; strict
                # rejection requires a lower bound exceeding the threshold.
                decision = ('accept_within_assumptions' if upper <= threshold
                            else 'reject_within_assumptions' if lower > threshold
                            else 'abstain')
                rows.append({'radius':d, 'preserve_group_size':preserve,
                    'status':'solved', 'decision':decision,
                    'min_errors':result['min_errors'], 'max_errors':result['max_errors'],
                    'lower_rate':lower, 'upper_rate':upper,
                    'lower_witness':result['lower_witness'],
                    'upper_witness':result['upper_witness'],
                    'membership_options':result['membership_options'],
                    'work':result['work']})
            except InfeasibleEvidence as exc:
                rows.append({'radius':d,'preserve_group_size':preserve,
                             'status':'infeasible','decision':'abstain','reason':str(exc)})
            except SearchLimit as exc:
                rows.append({'radius':d,'preserve_group_size':preserve,
                             'status':'resource_limited','decision':'abstain','reason':str(exc)})
    # An 'accept' at radius=0 is not sufficient if larger admissible models
    # reject/abstain. Missing or failed analyses block all definitive decisions.
    unique = {row['decision'] for row in rows}
    final = unique.pop() if len(unique) == 1 else 'abstain'
    return {'schema_version':1, 'max_error_rate':float(threshold),
        'overall_decision':final, 'scenarios':rows,
        'meaning':'conditional_partial_identification_not_confidence_interval',
        'provenance':'NOT_VERIFIED',
        'warning':'No evidence that true membership/cardinality/frame lies in tested envelopes; independent provenance is required.'}


def main():
    parser = argparse.ArgumentParser(description='Fail-closed conditional group-membership audit')
    parser.add_argument('input', type=Path, help='JSON audit request')
    parser.add_argument('--output', type=Path, help='Optional JSON output')
    args = parser.parse_args()
    try:
        result = audit(json.loads(args.input.read_text(encoding='utf-8')))
    except (InvalidEvidence, ValueError, TypeError, KeyError) as exc:
        result = {'overall_decision':'abstain','status':'invalid_input','reason':str(exc)}
    output = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(output + '\n', encoding='utf-8')
    else:
        print(output)
    return 0 if result.get('overall_decision') in ('accept_within_assumptions', 'reject_within_assumptions') else 2

if __name__ == '__main__':
    raise SystemExit(main())

"""Lumen 362: sharp bounds with explicitly enumerated uncertain memberships.

Assumptions: canonical entity frame; group values may be corrupted in <= k groups;
for groups in `candidates`, the TRUE membership is one of the enumerated
nonempty candidate subsets (including nominal). All other groups are trusted.
At most b candidate groups differ from nominal. Candidate authenticity and
pre-outcome commitment are EXTERNAL assumptions, not software guarantees.
Finite exhaustive search; limits raise without returning uncertified bounds.
"""
from itertools import product
from lumen360 import Group, InvalidEvidence, SearchLimit, InfeasibleEvidence, robust_bounds


def uncertain_membership_bounds(entities, reports, candidates, *,
                                max_membership_changes=0, max_corrupt_values=0,
                                max_scenarios=10000, max_nodes=250000):
    entities, reports = tuple(entities), tuple(reports)
    if not entities or any(type(e) is not str or not e for e in entities) or len(set(entities)) != len(entities):
        raise InvalidEvidence('unique nonempty canonical string entity IDs required')
    if any(type(x) is not int or x < 0 for x in (max_membership_changes, max_corrupt_values)):
        raise ValueError('corruption budgets must be nonnegative integers')
    if any(type(x) is not int or x < 1 for x in (max_scenarios, max_nodes)):
        raise ValueError('search budgets must be positive integers')
    if not isinstance(candidates, dict):
        raise InvalidEvidence('candidate map must be a dictionary')
    if len(set(g.name for g in reports)) != len(reports):
        raise InvalidEvidence('duplicate group names')
    names = {g.name for g in reports}
    if not set(candidates).issubset(names):
        raise InvalidEvidence('unknown candidate group')
    # Validate all reported values and memberships even if all reports may be corrupt.
    # No group changes are allowed during this validation.
    robust_bounds(entities, reports, max_corrupt=len(reports), max_nodes=max_nodes)
    choices = []
    for g in reports:
        nominal = frozenset(g.members)
        opts = [nominal]
        if g.name in candidates:
            raw = candidates[g.name]
            if not isinstance(raw, (tuple, list)) or not raw:
                raise InvalidEvidence(f'{g.name}: candidate options required')
            for members in raw:
                if isinstance(members, str):
                    raise InvalidEvidence(f'{g.name}: candidate must be a collection of IDs')
                members = tuple(members)
                if not members or len(set(members)) != len(members) or not set(members).issubset(entities):
                    raise InvalidEvidence(f'{g.name}: invalid candidate membership')
                fm = frozenset(members)
                if fm not in opts:
                    opts.append(fm)
        choices.append(opts)
    checked = 0
    total_nodes = 0
    lo = hi = None
    lower = upper = None
    feasible_scenarios = 0
    for variant in product(*choices):
        changes = sum(frozenset(g.members) != members for g, members in zip(reports, variant))
        if changes > max_membership_changes:
            continue
        checked += 1
        if checked > max_scenarios:
            raise SearchLimit('scenario budget exhausted; no certified bounds')
        # A count larger than a candidate membership is a forced corrupted
        # VALUE, not a malformed candidate. Reserve one unit of value budget.
        forced_bad = [g.name for g, members in zip(reports, variant)
                      if g.kind == 'count' and g.value > len(members)]
        if len(forced_bad) > max_corrupt_values:
            continue
        # Forced-bad reports impose no constraint on the underlying outcomes.
        changed = [Group(g.name, tuple(sorted(members)), g.kind, g.value)
                   for g, members in zip(reports, variant)
                   if g.name not in forced_bad]
        try:
            result = robust_bounds(entities, changed,
                                   max_corrupt=max_corrupt_values-len(forced_bad),
                                   max_nodes=max_nodes)
        except InfeasibleEvidence:
            continue
        total_nodes += result['nodes']
        feasible_scenarios += 1
        witness = {'membership': {g.name: sorted(m) for g,m in zip(reports,variant)},
                   'changes': changes, 'lower_assignment': result['lower_witness'],
                   'upper_assignment': result['upper_witness'],
                   'lower_disputed_values': forced_bad + result['lower_disputed_groups'],
                   'upper_disputed_values': forced_bad + result['upper_disputed_groups']}
        if lo is None or result['min_errors'] < lo:
            lo = result['min_errors']; lower = witness
        if hi is None or result['max_errors'] > hi:
            hi = result['max_errors']; upper = witness
    if lo is None:
        raise InfeasibleEvidence('no feasible assignments under stated budgets')
    return {'min_errors':lo, 'max_errors':hi, 'lower_rate':lo/len(entities),
            'upper_rate':hi/len(entities), 'scenarios_checked':checked,
            'feasible_scenarios':feasible_scenarios, 'nodes_in_feasible_scenarios':total_nodes,
            'lower_witness':lower, 'upper_witness':upper,
            'max_membership_changes':max_membership_changes,
            'max_corrupt_values':max_corrupt_values,
            'meaning':'sharp_partial_identification_not_confidence_interval',
            'candidate_set_independence':'NOT_VERIFIED_BY_SOFTWARE',
            'node_budget_scope':'per_scenario_not_global'}


def demo():
    entities = tuple('ABCDEF')
    groups = [Group('g0', ('A','B','C'), 'count', 1),
              Group('g1', ('B','C','D','F'), 'or', 1),
              Group('g2', ('B','C'), 'count', 0),
              Group('g3', ('C','F'), 'count', 0),
              Group('g4', ('A','B','D'), 'or', 1),
              Group('g5', ('B','E','F'), 'count', 1),
              Group('g6', ('A','B','C','F'), 'or', 1)]
    return {'trusted': uncertain_membership_bounds(entities, groups, {'g2':[('B','C'),('A','D')]},max_membership_changes=0),
            'one_uncertain': uncertain_membership_bounds(entities, groups, {'g2':[('B','C'),('A','D')]},max_membership_changes=1)}

if __name__=='__main__':
    import json
    print(json.dumps(demo(),indent=2))

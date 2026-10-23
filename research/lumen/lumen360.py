"""Sharp partial-identification bounds with at most k corrupted aggregate VALUES.

Binary canonical entities and authentic group memberships are assumed.
Not a confidence interval. Standard library only.
"""
from dataclasses import dataclass
from typing import Tuple

class InvalidEvidence(ValueError):
    pass

class SearchLimit(RuntimeError):
    pass

class InfeasibleEvidence(InvalidEvidence):
    pass

@dataclass(frozen=True)
class Group:
    name: str
    members: Tuple[str, ...]
    kind: str
    value: int

def robust_bounds(entities, groups, *, max_corrupt=0, trusted_memberships=None,
                  max_nodes=250_000):
    entities, groups = tuple(entities), tuple(groups)
    if not entities or len(set(entities)) != len(entities):
        raise InvalidEvidence('nonempty, unique canonical frame required')
    if type(max_corrupt) is not int or max_corrupt < 0:
        raise ValueError('max_corrupt must be a nonnegative integer')
    if type(max_nodes) is not int or max_nodes < 1:
        raise ValueError('max_nodes must be a positive integer')
    if len(set(g.name for g in groups)) != len(groups):
        raise InvalidEvidence('duplicate group names')
    lookup = {e: i for i, e in enumerate(entities)}
    compiled = []
    for g in groups:
        if not g.members or len(set(g.members)) != len(g.members):
            raise InvalidEvidence(f'{g.name}: empty or duplicate membership')
        if any(m not in lookup for m in g.members):
            raise InvalidEvidence(f'{g.name}: unknown entity')
        if g.kind not in ('or', 'count') or type(g.value) is not int:
            raise InvalidEvidence(f'{g.name}: bad kind/value')
        if g.kind == 'or' and g.value not in (0, 1):
            raise InvalidEvidence(f'{g.name}: OR value must be 0/1')
        if g.kind == 'count' and not 0 <= g.value <= len(g.members):
            raise InvalidEvidence(f'{g.name}: count outside feasible range')
        if trusted_memberships is not None and (
            g.name not in trusted_memberships or
            set(g.members) != set(trusted_memberships[g.name])
        ):
            raise InvalidEvidence(f'{g.name}: registry mismatch')
        compiled.append((tuple(lookup[e] for e in g.members), g.kind, g.value, g.name))
    if trusted_memberships is not None and set(trusted_memberships) != {g.name for g in groups}:
        raise InvalidEvidence('registry group set mismatch')

    n = len(entities)
    degree = [0] * n
    for ids, _, _, _ in compiled:
        for i in ids:
            degree[i] += 1
    order = sorted(range(n), key=lambda i: -degree[i])
    nodes = 0

    def mismatches(values, partial):
        bad = []
        for ids, kind, target, name in compiled:
            ones = sum(values[i] == 1 for i in ids)
            unknown = sum(values[i] == -1 for i in ids)
            if kind == 'count':
                mismatch = ones > target or ones + unknown < target
                if not partial:
                    mismatch = ones != target
            else:
                mismatch = (target == 0 and ones > 0) or (target == 1 and ones == 0 and unknown == 0)
            if mismatch:
                bad.append(name)
        return bad

    def optimize(minimize):
        nonlocal nodes
        best, best_assignment, best_bad = None, None, None
        def dfs(values, pos, known_ones):
            nonlocal nodes, best, best_assignment, best_bad
            nodes += 1
            if nodes > max_nodes:
                raise SearchLimit(f'exhausted {max_nodes} nodes; no certified bounds')
            if len(mismatches(values, True)) > max_corrupt:
                return
            remaining = n - pos
            if best is not None and (known_ones >= best if minimize else known_ones + remaining <= best):
                return
            if pos == n:
                bad = mismatches(values, False)
                if len(bad) <= max_corrupt and (best is None or
                    (known_ones < best if minimize else known_ones > best)):
                    best, best_assignment, best_bad = known_ones, values.copy(), bad
                return
            i = order[pos]
            for val in ((0, 1) if minimize else (1, 0)):
                values[i] = val
                dfs(values, pos + 1, known_ones + val)
            values[i] = -1
        dfs([-1] * n, 0, 0)
        return best, best_assignment, best_bad

    lo, lw, lb = optimize(True)
    hi, hw, hb = optimize(False)
    if lo is None:
        raise InfeasibleEvidence('no assignment matches all but max_corrupt group values')
    return {
        'min_errors': lo, 'max_errors': hi, 'lower_rate': lo / n,
        'upper_rate': hi / n, 'n_entities': n, 'n_groups': len(groups),
        'max_corrupt': max_corrupt, 'nodes': nodes,
        'lower_witness': dict(zip(entities, lw)),
        'upper_witness': dict(zip(entities, hw)),
        'lower_disputed_groups': lb, 'upper_disputed_groups': hb,
        'meaning': 'sharp_partial_identification_not_confidence_interval',
    }

def demo():
    entities = tuple('ABCDEF')
    groups = [
        Group('AB', ('A','B'), 'or', 1),
        Group('BC', ('B','C'), 'or', 1),
        Group('AC', ('A','C'), 'or', 1),
        Group('EF', ('E','F'), 'count', 1),
        Group('CD', ('C','D'), 'or', 0),
    ]
    return {f'k={k}': robust_bounds(entities, groups, max_corrupt=k) for k in (0,1,2)}

if __name__ == '__main__':
    import json
    print(json.dumps(demo(), indent=2, sort_keys=True))

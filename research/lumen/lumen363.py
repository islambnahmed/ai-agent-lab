"""Lumen 363: sensitivity envelope for omitted membership alternatives.

Enumerates all admissible true memberships within symmetric-difference radius d
of nominal groups. A DP over membership-change and value-corruption budgets
checks each binary outcome assignment. Results are sharp *conditional* partial-
identification bounds, not confidence intervals. This cannot attest provenance.
"""
from dataclasses import dataclass
from itertools import combinations

@dataclass(frozen=True)
class Report:
    name: str
    members: tuple[str, ...]
    kind: str
    value: int

class InvalidEvidence(ValueError): pass
class SearchLimit(RuntimeError): pass
class InfeasibleEvidence(ValueError): pass

def _iter_subsets_within_radius(n, nominal, radius, same_size):
    for flip in range(radius+1):
        for indices in combinations(range(n), flip):
            mask = nominal
            for i in indices: mask ^= 1 << i
            if mask and (not same_size or mask.bit_count() == nominal.bit_count()):
                yield mask

def _subsets_within_radius(n, nominal, radius, same_size):
    return sorted(set(_iter_subsets_within_radius(n, nominal, radius, same_size)))

def sensitivity_bounds(entities, reports, uncertain_groups, *, radius=0,
                       max_membership_changes=0, max_corrupt_values=0,
                       preserve_group_size=True, max_options=100_000,
                       max_work=3_000_000):
    entities, reports = tuple(entities), tuple(reports)
    if not entities or len(entities)>24 or any(not isinstance(e,str) or not e for e in entities) or len(set(entities))!=len(entities):
        raise InvalidEvidence('unique nonempty canonical entity IDs required')
    if not all(type(x) is int and x>=0 for x in (radius,max_membership_changes,max_corrupt_values)):
        raise InvalidEvidence('budgets and radius must be nonnegative integers')
    if not all(type(x) is int and x>0 for x in (max_options,max_work)):
        raise InvalidEvidence('positive resource limits required')
    if type(preserve_group_size) is not bool: raise InvalidEvidence('preserve_group_size must be bool')
    if radius>len(entities): raise InvalidEvidence('radius exceeds entity count')
    if len({r.name for r in reports})!=len(reports): raise InvalidEvidence('duplicate report names')
    if isinstance(uncertain_groups,str): raise InvalidEvidence('uncertain_groups must be a collection')
    uncertain_groups = tuple(uncertain_groups)
    if len(set(uncertain_groups))!=len(uncertain_groups) or not set(uncertain_groups).issubset({r.name for r in reports}):
        raise InvalidEvidence('unknown or duplicate uncertain group')
    index = {e:i for i,e in enumerate(entities)}
    options=[]
    total_options=0
    for r in reports:
        if not isinstance(r.name,str) or not r.name or not r.members or len(set(r.members))!=len(r.members) or any(e not in index for e in r.members):
            raise InvalidEvidence('bad report identity/membership')
        if r.kind not in ('or','count') or type(r.value) is not int or (r.kind=='or' and r.value not in (0,1)) or (r.kind=='count' and not 0<=r.value<=len(r.members)):
            raise InvalidEvidence('bad report value/kind')
        nominal=sum(1<<index[e] for e in r.members)
        opts = []
        for mask in (_iter_subsets_within_radius(len(entities),nominal,radius,preserve_group_size) if r.name in uncertain_groups else (nominal,)):
            total_options+=1
            if total_options>max_options: raise SearchLimit('membership option budget exceeded; no bounds')
            opts.append(mask)
        options.append((r,nominal,opts))
    min_err,max_err=None,None
    min_witness,max_witness=None,None
    work=0
    for y in range(1<<len(entities)):
        work+=1
        if work>max_work: raise SearchLimit('work budget exceeded; no bounds')
        states={(0,0): []}
        for r,nominal,opts in options:
            nxt={}
            for (changes,bad), path in states.items():
                for mask in opts:
                    work+=1
                    if work>max_work: raise SearchLimit('work budget exceeded; no bounds')
                    nc=changes+(mask!=nominal)
                    if nc>max_membership_changes: continue
                    prediction=(y&mask).bit_count() if r.kind=='count' else int(bool(y&mask))
                    nb=bad+(prediction!=r.value)
                    if nb<=max_corrupt_values and (nc,nb) not in nxt:
                        nxt[nc,nb]=path+[(r.name,mask,prediction!=r.value)]
            states=nxt
            if not states: break
        if not states: continue
        errors=y.bit_count()
        key=min(states)
        witness={'outcomes':{e:int(bool(y&(1<<i))) for i,e in enumerate(entities)},
                 'membership':{name:[entities[i] for i in range(len(entities)) if mask&(1<<i)] for name,mask,_ in states[key]},
                 'corrupted_reports':[name for name,_,bad in states[key] if bad],
                 'membership_changes':key[0], 'value_corruptions':key[1]}
        if min_err is None or errors<min_err: min_err,min_witness=errors,witness
        if max_err is None or errors>max_err: max_err,max_witness=errors,witness
    if min_err is None: raise InfeasibleEvidence('no feasible outcome and membership assignment')
    n=len(entities)
    return {'min_errors':min_err,'max_errors':max_err,'lower_rate':min_err/n,'upper_rate':max_err/n,
            'lower_witness':min_witness,'upper_witness':max_witness,'work':work,
            'membership_options':total_options,'radius':radius,
            'max_membership_changes':max_membership_changes,
            'max_corrupt_values':max_corrupt_values,'preserve_group_size':preserve_group_size,
            'meaning':'sharp_conditional_partial_identification_not_confidence_interval',
            'provenance':'NOT_VERIFIED'}

def demo():
    entities=tuple('ABCDEF')
    reports=[Report('g0',('A','B','C'),'count',1),Report('g1',('B','C','D','F'),'or',1),
             Report('g2',('B','C'),'count',0),Report('g3',('C','F'),'count',0),
             Report('g4',('A','B','D'),'or',1),Report('g5',('B','E','F'),'count',1),
             Report('g6',('A','B','C','F'),'or',1)]
    authentic={f'radius_{d}':sensitivity_bounds(entities,reports,{'g2'},radius=d,max_membership_changes=1)
            for d in (0,2,4)}
    altered=[Report(r.name, ('A','D') if r.name=='g2' else r.members, r.kind, r.value) for r in reports]
    self_attested={f'radius_{d}':sensitivity_bounds(entities,altered,{'g2'},radius=d,max_membership_changes=1)
            for d in (0,2,4)}
    return {'authentic_nominal':authentic,'self_attested_altered_nominal':self_attested}

if __name__=='__main__':
    import json
    print(json.dumps(demo(),indent=2))

import itertools
import random
import unittest
from lumen363 import Report,sensitivity_bounds,InvalidEvidence,SearchLimit,InfeasibleEvidence,_subsets_within_radius,demo

# Independent oracle: explicit Cartesian product over memberships AND outcomes.
def oracle(entities,reports,uncertain,radius,b,k,preserve=True):
    n=len(entities)
    index={e:i for i,e in enumerate(entities)}
    choices=[]
    for r in reports:
        mask=sum(1<<index[e] for e in r.members)
        choices.append((r,mask,_subsets_within_radius(n,mask,radius,preserve) if r.name in uncertain else [mask]))
    feasible=[]
    for memberships in itertools.product(*(v for _,_,v in choices)):
        if sum(mask!=nominal for mask,(_,nominal,_) in zip(memberships,choices))>b:continue
        for outcome in range(1<<n):
            bad=sum(((outcome&mask).bit_count() if r.kind=='count' else int(bool(outcome&mask)))!=r.value for mask,(r,_,_) in zip(memberships,choices))
            if bad<=k: feasible.append(outcome.bit_count())
    return (min(feasible),max(feasible)) if feasible else None

class Tests(unittest.TestCase):
    def test_demo_baseline_and_widening(self):
        d=demo()['authentic_nominal']
        self.assertEqual((d['radius_0']['min_errors'],d['radius_0']['max_errors']),(3,3))
        self.assertTrue(d['radius_0']['min_errors']>=d['radius_2']['min_errors']>=d['radius_4']['min_errors'])
        self.assertTrue(d['radius_0']['max_errors']<=d['radius_2']['max_errors']<=d['radius_4']['max_errors'])
        self.assertLessEqual(d['radius_4']['min_errors'],1)
        for x in d.values():
            for key,w in (('min_errors',x['lower_witness']),('max_errors',x['upper_witness'])):
                self.assertEqual(sum(w['outcomes'].values()),x[key])
                self.assertLessEqual(w['membership_changes'],1)
                self.assertEqual(w['value_corruptions'],0)
    def test_false_accept_reversed_nominal(self):
        d=demo()['self_attested_altered_nominal']
        self.assertEqual([(d[f'radius_{x}']['min_errors'],d[f'radius_{x}']['max_errors']) for x in (0,2,4)],[(1,1),(1,2),(1,3)])
        self.assertEqual(d['radius_4']['upper_witness']['membership']['g2'],['B','C'])
    def test_randomized_independent_oracle(self):
        rng=random.Random(363)
        for case in range(350):
            n=rng.randint(2,4); entities=tuple('ABCD'[:n]); m=rng.randint(1,3)
            reports=[]
            for i in range(m):
                members=tuple(e for e in entities if rng.random()<0.6) or (entities[0],)
                kind=rng.choice(['count','or']); value=rng.randint(0,len(members)) if kind=='count' else rng.randint(0,1)
                reports.append(Report(f'g{i}',members,kind,value))
            uncertain=set(r.name for r in reports if rng.random()<0.6)
            radius=rng.randint(0,2); b=rng.randint(0,1); k=rng.randint(0,1); preserve=rng.choice([True,False])
            expected=oracle(entities,reports,uncertain,radius,b,k,preserve)
            if expected is None:
                with self.assertRaises(InfeasibleEvidence):sensitivity_bounds(entities,reports,uncertain,radius=radius,max_membership_changes=b,max_corrupt_values=k,preserve_group_size=preserve)
            else:
                got=sensitivity_bounds(entities,reports,uncertain,radius=radius,max_membership_changes=b,max_corrupt_values=k,preserve_group_size=preserve)
                self.assertEqual((got['min_errors'],got['max_errors']),expected,(case,got))
    def test_invalid_inputs_and_budget(self):
        r=[Report('g',('A',),'count',1)]
        for args in [dict(radius=-1),dict(max_membership_changes=True),dict(max_corrupt_values=-1),dict(radius=3)]:
            with self.assertRaises(InvalidEvidence):sensitivity_bounds(('A','B'),r,{'g'},**args)
        with self.assertRaises(InvalidEvidence):sensitivity_bounds(('A','B'),r,{'unknown'})
        with self.assertRaises(InvalidEvidence):sensitivity_bounds(('A','A'),r,{'g'})
        with self.assertRaises(SearchLimit):sensitivity_bounds(('A','B'),r,{'g'},radius=2,preserve_group_size=False,max_options=1)
        with self.assertRaises(SearchLimit):sensitivity_bounds(('A','B'),r,{'g'},max_work=1)
        with self.assertRaises(SearchLimit):sensitivity_bounds(tuple('ABCDEFGHIJKLMNOPQRST'),[],set(),max_work=2)
        with self.assertRaises(InvalidEvidence):sensitivity_bounds(tuple(str(i) for i in range(25)),[],set())
    def test_unconstrained_all_possible(self):
        x=sensitivity_bounds(('A','B','C'),[],set())
        self.assertEqual((x['min_errors'],x['max_errors']),(0,3))
    def test_monotonic_corruption_budget(self):
        entities=('A','B','C')
        r=[Report('a',('A','B'),'count',1),Report('b',('B','C'),'count',0)]
        low=sensitivity_bounds(entities,r,{'a'},radius=2,max_membership_changes=1,max_corrupt_values=0)
        high=sensitivity_bounds(entities,r,{'a'},radius=2,max_membership_changes=1,max_corrupt_values=1)
        self.assertLessEqual(high['min_errors'],low['min_errors'])
        self.assertGreaterEqual(high['max_errors'],low['max_errors'])

if __name__=='__main__':unittest.main()

import itertools
import random
import unittest
from lumen360 import Group, InvalidEvidence, InfeasibleEvidence, SearchLimit
from lumen362 import uncertain_membership_bounds, demo


def oracle(entities, reports, candidates, b, k):
    opts = [[frozenset(g.members)] + [frozenset(x) for x in candidates.get(g.name, [])
             if frozenset(x) != frozenset(g.members)] for g in reports]
    totals = []
    for variants in itertools.product(*opts):
        if sum(frozenset(g.members)!=v for g,v in zip(reports,variants))>b: continue
        for bits in itertools.product((0,1),repeat=len(entities)):
            d=dict(zip(entities,bits)); bad=0
            for g,m in zip(reports,variants):
                count=sum(d[x] for x in m)
                actual=int(count>0) if g.kind=='or' else count
                bad+=actual!=g.value
            if bad<=k: totals.append(sum(bits))
    if not totals: raise InfeasibleEvidence('oracle infeasible')
    return min(totals),max(totals)


class Tests(unittest.TestCase):
    def test_attack_bounds(self):
        d=demo()
        self.assertEqual((d['trusted']['min_errors'],d['trusted']['max_errors']),(3,3))
        self.assertEqual((d['one_uncertain']['min_errors'],d['one_uncertain']['max_errors']),(1,3))
        self.assertEqual(d['one_uncertain']['scenarios_checked'],2)

    def test_witnesses(self):
        d=demo()['one_uncertain']
        for side in ('lower','upper'):
            w=d[side+'_witness']
            a=w[side+'_assignment']
            self.assertEqual(sum(a.values()),d['min_errors' if side=='lower' else 'max_errors'])
            self.assertLessEqual(w['changes'],1)

    def test_infeasible(self):
        with self.assertRaises(InfeasibleEvidence):
            uncertain_membership_bounds(('A',),[Group('x',('A',),'count',0),Group('y',('A',),'count',1)],{},max_membership_changes=0)

    def test_scenario_limit_fails_closed(self):
        with self.assertRaises(SearchLimit):
            uncertain_membership_bounds(('A','B'),[Group('g',('A',),'or',1)],{'g':[('B',)]},max_membership_changes=1,max_scenarios=1)

    def test_node_limit_fails_closed(self):
        with self.assertRaises(SearchLimit):
            uncertain_membership_bounds(('A','B','C'),[Group('g',('A',),'or',1)],{},max_nodes=1)

    def test_invalid_candidate(self):
        for candidate in ([('Z',)], [('A','A')], [()], ['AB']):
            with self.assertRaises(InvalidEvidence):
                uncertain_membership_bounds(('A','B'),[Group('g',('A',),'or',1)],{'g':candidate},max_membership_changes=1)

    def test_unknown_group(self):
        with self.assertRaises(InvalidEvidence):
            uncertain_membership_bounds(('A',),[Group('g',('A',),'or',1)],{'other':[('A',)]})

    def test_invalid_report_even_with_value_budget(self):
        with self.assertRaises(InvalidEvidence):
            uncertain_membership_bounds(('A',),[Group('g',('A',),'count',2)],{},max_corrupt_values=1)

    def test_monotonicity(self):
        groups=[Group('x',('A','B'),'or',1),Group('y',('B','C'),'count',0)]
        candidates={'x':[('A',),('C',)]}
        a=uncertain_membership_bounds(tuple('ABC'),groups,candidates,max_membership_changes=0,max_corrupt_values=1)
        b=uncertain_membership_bounds(tuple('ABC'),groups,candidates,max_membership_changes=1,max_corrupt_values=1)
        self.assertGreaterEqual(a['min_errors'],b['min_errors'])
        self.assertLessEqual(a['max_errors'],b['max_errors'])

    def test_out_of_range_count_is_forced_corrupt_and_unconstraining(self):
        # Nominal two-member COUNT=2; alternate singleton makes the
        # reported value necessarily false, irrespective of its true outcome.
        entities=('A','B')
        reports=[Group('g',('A','B'),'count',2)]
        candidates={'g':[('A',)]}
        result=uncertain_membership_bounds(entities,reports,candidates,
                                           max_membership_changes=1,max_corrupt_values=1)
        self.assertEqual((result['min_errors'],result['max_errors']),(0,2))
        self.assertIn('g',result['lower_witness']['lower_disputed_values'])

    def test_randomized_oracle(self):
        rng=random.Random(362)
        for case in range(250):
            n=rng.randrange(2,7); entities=tuple(f'e{i}' for i in range(n))
            reports=[]; candidates={}
            for j in range(rng.randrange(1,5)):
                m=tuple(sorted(rng.sample(entities,rng.randint(1,n))))
                kind=rng.choice(('or','count'))
                value=rng.randrange(2) if kind=='or' else rng.randrange(len(m)+1)
                g=Group(f'g{j}',m,kind,value); reports.append(g)
                if rng.random()<0.6:
                    candidates[g.name]=[tuple(sorted(rng.sample(entities,rng.randint(1,n))))]
            b=rng.randrange(2); k=rng.randrange(2)
            try: expected=oracle(entities,reports,candidates,b,k)
            except InfeasibleEvidence:
                with self.assertRaises(InfeasibleEvidence):
                    uncertain_membership_bounds(entities,reports,candidates,max_membership_changes=b,max_corrupt_values=k)
            else:
                result=uncertain_membership_bounds(entities,reports,candidates,max_membership_changes=b,max_corrupt_values=k)
                self.assertEqual((result['min_errors'],result['max_errors']),expected,(case,reports,candidates,b,k))

if __name__=='__main__': unittest.main(verbosity=2)

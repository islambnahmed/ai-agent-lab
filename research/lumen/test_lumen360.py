import itertools
import random
import unittest
from lumen360 import Group, robust_bounds, InvalidEvidence, InfeasibleEvidence, SearchLimit, demo

def oracle(entities, groups, k):
    outcomes = []
    for bits in itertools.product((0,1), repeat=len(entities)):
        state = dict(zip(entities, bits))
        bad = []
        for g in groups:
            value = int(any(state[x] for x in g.members)) if g.kind == 'or' else sum(state[x] for x in g.members)
            if value != g.value:
                bad.append(g.name)
        if len(bad) <= k:
            outcomes.append((sum(bits),state,bad))
    return outcomes

class TestRobust(unittest.TestCase):
    def test_clean_and_relaxed(self):
        d=demo()
        self.assertEqual((d['k=0']['min_errors'],d['k=0']['max_errors']),(3,3))
        for k in (1,2):
            self.assertLessEqual(d[f'k={k}']['min_errors'],d[f'k={k-1}']['min_errors'])
            self.assertGreaterEqual(d[f'k={k}']['max_errors'],d[f'k={k-1}']['max_errors'])

    def test_exact_oracle_500_cases(self):
        rng=random.Random(360)
        for t in range(500):
            n=rng.randint(2,8)
            es=tuple(f'e{i}' for i in range(n))
            gs=[]
            for j in range(rng.randint(0,10)):
                members=tuple(rng.sample(es,rng.randint(1,n)))
                kind=rng.choice(('or','count'))
                gs.append(Group(f'g{j}',members,kind,rng.randint(0,1 if kind=='or' else len(members))))
            k=rng.randint(0, min(3,len(gs)))
            expected=oracle(es,gs,k)
            if not expected:
                with self.assertRaises(InfeasibleEvidence):
                    robust_bounds(es,gs,max_corrupt=k)
            else:
                result=robust_bounds(es,gs,max_corrupt=k)
                self.assertEqual((result['min_errors'],result['max_errors']),
                                 (min(v[0] for v in expected),max(v[0] for v in expected)),t)
                for suffix in ('lower','upper'):
                    witness=result[f'{suffix}_witness']
                    bad=result[f'{suffix}_disputed_groups']
                    self.assertIn((sum(witness.values()),witness,bad),expected)

    def test_contradiction_tolerated_only_with_budget(self):
        gs=[Group('yes',('a',),'or',1),Group('no',('a',),'or',0)]
        with self.assertRaises(InfeasibleEvidence):
            robust_bounds(('a',),gs,max_corrupt=0)
        self.assertEqual((robust_bounds(('a',),gs,max_corrupt=1)['min_errors'],
                          robust_bounds(('a',),gs,max_corrupt=1)['max_errors']),(0,1))

    def test_registry_mismatch_rejected_even_with_large_k(self):
        with self.assertRaisesRegex(InvalidEvidence,'registry mismatch'):
            robust_bounds(('a','b'),[Group('g',('a',),'or',1)],max_corrupt=20,
                          trusted_memberships={'g':('b',)})

    def test_out_of_range_cannot_be_repaired_as_corrupt_value(self):
        with self.assertRaises(InvalidEvidence):
            robust_bounds(('a',),[Group('g',('a',),'count',3)],max_corrupt=1)

    def test_boolean_k_rejected(self):
        with self.assertRaises(ValueError):
            robust_bounds(('a',),[],max_corrupt=True)

    def test_budget_fail_closed(self):
        with self.assertRaises(SearchLimit):
            robust_bounds(tuple('abcdef'),[],max_nodes=1)

    def test_empty_groups(self):
        r=robust_bounds(('a','b'),[],max_corrupt=0)
        self.assertEqual((r['min_errors'],r['max_errors']),(0,2))

    def test_duplicate_group(self):
        with self.assertRaises(InvalidEvidence):
            robust_bounds(('a',),[Group('g',('a',),'or',0),Group('g',('a',),'or',1)])

    def test_untrusted_membership_not_proven(self):
        gs=[Group('g',('a',),'or',1)]
        r=robust_bounds(('a','b'),gs,max_corrupt=0)
        self.assertEqual((r['min_errors'],r['max_errors']),(1,2))
        self.assertNotIn('attested',r)

if __name__=='__main__':
    unittest.main(verbosity=2)

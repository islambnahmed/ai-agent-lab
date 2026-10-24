import copy
import itertools
import unittest
from provenance_gate import policy,policy_hash,evaluate
from quorum_gate import policy as old_policy,policy_hash as old_hash,evaluate as old_evaluate

class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.domains={'x1':'X','x2':'X','x3':'X','y':'Y','z':'Z'}
        self.slots=[('crawl',str(i)) for i in range(14)]
        self.p=policy('seo',['agent'],self.slots,self.domains)
        self.a=policy_hash(self.p)

    def receipts(self,poison=(),missing=(),disagree=()):
        rows=[]
        for i,(source,slot) in enumerate(self.slots):
            truth=[0,1] if i%2 else [1,0]
            for w in self.domains:
                if w in missing: continue
                v=[0,1] if self.domains[w] in poison or w in disagree else truth
                rows.append({'witness':w,'source':source,'slot':slot,'measurements':{'agent':v}})
        return rows

    def old(self,rows):
        p=old_policy('seo',['agent'],self.slots,list(self.domains),3)
        return old_evaluate(p,old_hash(p),rows)

    def test_honest_same_result(self):
        rows=self.receipts()
        self.assertEqual(evaluate(self.p,self.a,rows).source_result,self.old(rows).source_result)

    def test_common_mode_majority_witness_fools_old_not_new(self):
        rows=self.receipts(poison=('X',))
        self.assertIn('agent',self.old(rows).source_result.first_crossings)
        self.assertNotIn('agent',evaluate(self.p,self.a,rows).source_result.first_crossings)

    def test_two_compromised_domains_can_fool_new(self):
        rows=self.receipts(poison=('X','Y'))
        self.assertIn('agent',evaluate(self.p,self.a,rows).source_result.first_crossings)

    def test_internal_disagreement_abstains(self):
        rows=self.receipts(disagree=('x1',))
        r=evaluate(self.p,self.a,rows)
        self.assertEqual(r.domain_disagreements,7)
        self.assertNotIn('agent',r.source_result.first_crossings)

    def test_missing_domain_blocks_without_two_agreeing(self):
        rows=self.receipts(poison=('X',),missing=('z',))
        with self.assertRaisesRegex(ValueError,'no independent domain quorum'):
            evaluate(self.p,self.a,rows)

    def test_missing_compromised_domain_keeps_honest_quorum(self):
        rows=self.receipts(poison=('X',),missing=('x1','x2','x3'))
        r=evaluate(self.p,self.a,rows)
        self.assertEqual(r.missing_domain_opportunities,14)

    def test_policy_binding(self):
        for field,val in [('domain_quorum',1),('witness_domains',{'x1':'a','x2':'b','x3':'c','y':'d','z':'e'})]:
            p=copy.deepcopy(self.p);p[field]=val
            with self.subTest(field=field),self.assertRaises(ValueError):
                evaluate(p,self.a,self.receipts())

    def test_reject_bad_receipts(self):
        rows=self.receipts()
        cases=[]
        cases.append(rows+[rows[0]])
        r=copy.deepcopy(rows);r[0]['witness']='unknown';cases.append(r)
        r=copy.deepcopy(rows);r[0]['measurements']['agent']=[True,1];cases.append(r)
        r=copy.deepcopy(rows);r[0]['slot']='unknown';cases.append(r)
        for case in cases:
            with self.subTest(case=case[0]),self.assertRaises(ValueError):
                evaluate(self.p,self.a,case)

    def test_two_domains_one_corrupt_abstains(self):
        dom={'a':'X','b':'X','c':'Y'}
        p=policy('small',['agent'],self.slots,dom)
        rows=[r for r in self.receipts(poison=('X',)) if r['witness'] in ('x1','x2','y')]
        rename={'x1':'a','x2':'b','y':'c'}
        for r in rows:r['witness']=rename[r['witness']]
        with self.assertRaisesRegex(ValueError,'no independent domain quorum'):
            evaluate(p,policy_hash(p),rows)

    def test_exhaustive_domain_vote_3_states(self):
        p=policy('exact',['agent'],[('s','0')],{'a':'A','b':'B','c':'C'})
        for states in itertools.product(('honest','forged','missing'),repeat=3):
            rows=[]
            for w,state in zip(('a','b','c'),states):
                if state=='missing':continue
                rows.append({'witness':w,'source':'s','slot':'0','measurements':{'agent':[1,0] if state=='honest' else [0,1]}})
            with self.subTest(states=states):
                if max(states.count('honest'),states.count('forged')) < 2:
                    with self.assertRaises(ValueError):evaluate(p,policy_hash(p),rows)
                else:
                    r=evaluate(p,policy_hash(p),rows)
                    self.assertEqual(r.resolved_candidate_observations,1)

    def test_real_improvement_still_crosses(self):
        rows=[]
        for source,slot in self.slots:
            for w in self.domains:
                rows.append({'witness':w,'source':source,'slot':slot,
                             'measurements':{'agent':[0,1]}})
        self.assertIn('agent',evaluate(self.p,self.a,rows).source_result.first_crossings)

    def test_finance_two_candidates_transfer(self):
        p=policy('finance',['a','b'],[('ledger',str(i)) for i in range(14)],self.domains)
        rows=[]
        for i in range(14):
            for w,domain in self.domains.items():
                truth=[5000,6000] if i%2 else [6000,5000]
                rows.append({'witness':w,'source':'ledger','slot':str(i),
                             'measurements':{'a':[5000,10000] if domain=='X' else truth,
                                             'b':truth}})
        r=evaluate(p,policy_hash(p),rows)
        self.assertEqual(r.resolved_candidate_observations,28)
        self.assertNotIn('a',r.source_result.first_crossings)
        self.assertNotIn('b',r.source_result.first_crossings)

    def test_declared_domain_splitting_is_counterexample(self):
        # False provenance can defeat the rule: 3 correlated witnesses are
        # misdeclared as independent, so no cryptographic assurance exists.
        fake={'x1':'X1','x2':'X2','x3':'X3','y':'Y','z':'Z'}
        p=policy('seo',['agent'],self.slots,fake)
        self.assertIn('agent',evaluate(p,policy_hash(p),self.receipts(poison=('X',))).source_result.first_crossings)

if __name__=='__main__':unittest.main()

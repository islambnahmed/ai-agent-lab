import copy
import itertools
import math
import unittest
from quorum_gate import policy,policy_hash,evaluate,score
from baseline_manifest_gate import evaluate as baseline_evaluate, commitment

class QuorumGateTests(unittest.TestCase):
    def setUp(self):
        self.p=policy('seo',['agentA'],[('crawl',str(i)) for i in range(12)],['a','b','c'],2)
        self.anchor=policy_hash(self.p)
        self.honest=self.receipts()

    def receipts(self,signs=None):
        signs=signs or [-1 if i%2 else 1 for i in range(12)]
        return [{'witness':w,'source':'crawl','slot':str(i),
                 'measurements':{'agentA':[0,1] if s>0 else [1,0]}}
                for w in ['a','b','c'] for i,s in enumerate(signs)]

    def test_all_honest(self):
        r=evaluate(self.p,self.anchor,self.honest)
        self.assertEqual(r.resolved_candidate_observations,12)
        self.assertEqual(r.dissenting_witness_values,0)
        self.assertEqual(r.missing_witness_slots,0)
        self.assertNotIn('agentA',r.source_result.first_crossings)

    def test_one_forged_witness_does_not_change_result(self):
        forged=copy.deepcopy(self.honest)
        for r in forged:
            if r['witness']=='c':r['measurements']['agentA']=[0,1]
        clean=evaluate(self.p,self.anchor,self.honest)
        attacked=evaluate(self.p,self.anchor,forged)
        self.assertEqual(clean.source_result,attacked.source_result)
        self.assertEqual(attacked.dissenting_witness_values,6)

    def test_two_colluding_witnesses_can_forge(self):
        forged=copy.deepcopy(self.honest)
        for r in forged:
            if r['witness'] in ('b','c'):r['measurements']['agentA']=[0,1]
        attacked=evaluate(self.p,self.anchor,forged)
        self.assertIn('agentA',attacked.source_result.first_crossings)
        self.assertEqual(attacked.dissenting_witness_values,6)

    def test_one_witness_missing_still_works(self):
        remaining=[r for r in self.honest if r['witness']!='c']
        r=evaluate(self.p,self.anchor,remaining)
        self.assertEqual(r.missing_witness_slots,12)
        self.assertEqual(r.source_result,evaluate(self.p,self.anchor,self.honest).source_result)

    def test_one_honest_missing_and_one_forged_fails_closed(self):
        remaining=[copy.deepcopy(r) for r in self.honest if r['witness']!='b']
        for r in remaining:
            if r['witness']=='c':r['measurements']['agentA']=[0,1]
        with self.assertRaisesRegex(ValueError,'no independent quorum'):
            evaluate(self.p,self.anchor,remaining)

    def test_all_honest_missing_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'no independent quorum'):
            evaluate(self.p,self.anchor,[])

    def test_policy_tampering_rejected(self):
        for field,value in [('quorum',3),('witnesses',['a','b','d']),('metric','unbounded')]:
            changed=copy.deepcopy(self.p);changed[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                evaluate(changed,self.anchor,self.honest)

    def test_duplicate_receipts_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):
            evaluate(self.p,self.anchor,self.honest+[self.honest[0]])

    def test_unknown_witness_and_slot_rejected(self):
        for key,value in [('witness','fake'),('slot','999')]:
            changed=copy.deepcopy(self.honest);changed[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                evaluate(self.p,self.anchor,changed)

    def test_invalid_raw_data_rejected(self):
        for pair in ([True,1],[-1,1],[0,10001],[0,1.0],[0],[float('nan'),1]):
            changed=copy.deepcopy(self.honest);changed[0]['measurements']['agentA']=pair
            with self.subTest(pair=pair),self.assertRaises(ValueError):
                evaluate(self.p,self.anchor,changed)

    def test_invalid_policy_quorum_rejected(self):
        for witnesses,q in [(['a','b'],2),(['a','b','c'],1),(['a','a','b'],2),(['a','b','c'],True)]:
            with self.subTest(witnesses=witnesses,q=q),self.assertRaises(ValueError):
                policy('bad',['agentA'],[('crawl','0')],witnesses,q)

    def test_exact_fair_sign_enumeration(self):
        p=policy('exact',['agentA'],[('source',str(i)) for i in range(9)],['a','b','c'],2)
        a=policy_hash(p)
        mean_e=0;crossings=0
        for signs in itertools.product((-1,1),repeat=9):
            rows=[{'witness':w,'source':'source','slot':str(i),'measurements':{'agentA':[0,1] if s>0 else [1,0]}}
                  for w in ['a','b','c'] for i,s in enumerate(signs)]
            r=evaluate(p,a,rows,alpha=.2)
            mean_e+=math.exp(r.source_result.final_log_e['agentA'])
            crossings+=int('agentA' in r.source_result.first_crossings)
        self.assertLessEqual(mean_e/512,1+1e-12)
        self.assertLessEqual(crossings/512,.2)

    def test_exhaustive_one_slot_three_witness_states(self):
        # 3^3 combinations: honest, adversarial, or missing per witness.
        # For two honest sources, the result must be honest regardless of the third.
        p=policy('exhaustive',['agentA'],[('source','one')],['a','b','c'],2)
        anchor=policy_hash(p)
        for states in itertools.product(('honest','forged','missing'),repeat=3):
            receipts=[]
            for w,state in zip(('a','b','c'),states):
                if state=='missing':continue
                pair=[1,0] if state=='honest' else [0,1]
                receipts.append({'witness':w,'source':'source','slot':'one',
                                 'measurements':{'agentA':pair}})
            honest=states.count('honest');forged=states.count('forged')
            with self.subTest(states=states):
                if max(honest,forged)<2:
                    with self.assertRaisesRegex(ValueError,'no independent quorum'):
                        evaluate(p,anchor,receipts)
                else:
                    result=evaluate(p,anchor,receipts,lambdas=(.8,))
                    expected=math.log1p(-.8 if honest>=2 else .8)
                    self.assertAlmostEqual(result.source_result.final_log_e['agentA'],expected)

    def test_multi_candidate_quorum_independent(self):
        p=policy('finance',['agentA','agentB'],[('ledger','one')],['a','b','c'],2)
        receipts=[
            {'witness':'a','source':'ledger','slot':'one','measurements':{'agentA':[1,0],'agentB':[0,1]}},
            {'witness':'b','source':'ledger','slot':'one','measurements':{'agentA':[1,0],'agentB':[1,0]}},
            {'witness':'c','source':'ledger','slot':'one','measurements':{'agentA':[0,1],'agentB':[0,1]}},
        ]
        result=evaluate(p,policy_hash(p),receipts,lambdas=(.8,))
        self.assertEqual(result.dissenting_witness_values,2)
        self.assertAlmostEqual(result.source_result.final_log_e['agentA'],math.log(.2))
        self.assertAlmostEqual(result.source_result.final_log_e['agentB'],math.log(1.8))

    def test_pair_score_bounded(self):
        for before in [0,1,9999,10000]:
            for after in [0,1,9999,10000]:
                self.assertLessEqual(abs(score((before,after))),1)

    def test_baseline_forged_agent_rows_cross(self):
        fake=[{'source':'crawl','slot':str(i),'scores':{'agentA':1}} for i in range(12)]
        result=baseline_evaluate(self.p['manifest'],commitment(self.p['manifest']),fake,lambdas=(.8,))
        self.assertIn('agentA',result.first_crossings)

if __name__=='__main__':unittest.main()

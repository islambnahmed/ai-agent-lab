import unittest
import copy
import itertools
import math
from manifest_gate import manifest,commitment,evaluate,naive_reindexed

class ManifestGateTests(unittest.TestCase):
    def setUp(self):
        self.m = manifest('seo-ab', ['agentA','agentB'], [('crawl',f'url-{i}') for i in range(20)])
        self.anchor = commitment(self.m)

    def test_hash_stable_for_dict_key_order(self):
        reordered = dict(reversed(list(self.m.items())))
        self.assertEqual(self.anchor, commitment(reordered))

    def test_tampered_schedule_rejected(self):
        for change in ('drop','reorder','relabel','candidate'):
            m=copy.deepcopy(self.m)
            if change=='drop': m['slots'].pop()
            if change=='reorder': m['slots'].reverse()
            if change=='relabel': m['slots'][0][1]='fake'
            if change=='candidate': m['candidates'][0]='other'
            with self.subTest(change=change),self.assertRaises(ValueError):evaluate(m,self.anchor,[])

    def test_omitted_rounds_are_missing_not_renumbered(self):
        events=[{'source':'crawl','slot':f'url-{i}','scores':{'agentA':1}} for i in range(0,20,2)]
        result=evaluate(self.m,self.anchor,events,lambdas=(.8,))
        naive=naive_reindexed(events,['agentA','agentB'],lambdas=(.8,))
        self.assertEqual(result.missing_opportunities,10)
        self.assertEqual(result.missing_scores,{'agentA':10,'agentB':20})
        self.assertNotIn('agentA',result.first_crossings)
        self.assertIn('agentA',naive.first_crossings)

    def test_duplicate_and_unknown_slots_fail_closed(self):
        ev={'source':'crawl','slot':'url-1','scores':{'agentA':1}}
        with self.assertRaises(ValueError):evaluate(self.m,self.anchor,[ev,ev])
        with self.assertRaises(ValueError):evaluate(self.m,self.anchor,[{**ev,'slot':'url-100'}])

    def test_unregistered_candidate_and_invalid_score(self):
        for scores in ({'other':1},{'agentA':True},{'agentA':float('nan')},{'agentA':2}):
            with self.subTest(scores=scores),self.assertRaises(ValueError):
                evaluate(self.m,self.anchor,[{'source':'crawl','slot':'url-1','scores':scores}])

    def test_missing_scores_counted_per_roster(self):
        ev={'source':'crawl','slot':'url-1','scores':{'agentA':1,'agentB':None}}
        res=evaluate(self.m,self.anchor,[ev])
        self.assertEqual(res.missing_scores,{'agentA':19,'agentB':20})

    def test_out_of_order_events_reconcile(self):
        events=[{'source':'crawl','slot':f'url-{i}','scores':{'agentA':(-1)**i}} for i in range(20)]
        self.assertEqual(evaluate(self.m,self.anchor,events),evaluate(self.m,self.anchor,events[::-1]))

    def test_malformed_manifest_and_config(self):
        for kwargs in ({'alpha':True},{'alpha':1},{'lambdas':(1,)},{'lambdas':(float('nan'),)}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):evaluate(self.m,self.anchor,[],**kwargs)
        for slots in ([('crawl','same'),('crawl','same')], [('crawl',1)]):
            with self.assertRaises(ValueError):manifest('bad',['a'],slots)

    def test_wrong_anchor_fails(self):
        with self.assertRaises(ValueError):evaluate(self.m,'0'*64,[])

    def test_exact_fair_signs_selective_round_omission(self):
        # 2^10 equally likely independent fair signs, log negative rounds only.
        # With the anchored roster of 10 opportunities, the e-process remains
        # an e-value even under outcome-dependent complete-round suppression.
        n=10
        m=manifest('exact',['agentA'], [('source',str(i)) for i in range(n)])
        anchor=commitment(m)
        mean_e=0.0
        any_cross=0
        for signs in itertools.product((-1,1),repeat=n):
            events=[{'source':'source','slot':str(i),'scores':{'agentA':x}}
                    for i,x in enumerate(signs) if x>0]
            r=evaluate(m,anchor,events,alpha=.2,lambdas=(.8,))
            mean_e+=math.exp(r.final_log_e['agentA'])
            any_cross+=int('agentA' in r.first_crossings)
        self.assertLessEqual(mean_e/2**n,1+1e-12)
        self.assertLessEqual(any_cross/2**n,.2)

    def test_forged_scores_are_not_detected(self):
        # An attacker who can falsify measurements, not just drop rows, still wins.
        forged=[{'source':'crawl','slot':f'url-{i}','scores':{'agentA':1}} for i in range(20)]
        result=evaluate(self.m,self.anchor,forged,lambdas=(.8,))
        self.assertIn('agentA',result.first_crossings)

    def test_unanchored_precommit_omission_is_undetectable(self):
        # Hashing an incomplete manifest cannot prove source opportunity coverage.
        incomplete=manifest('seo-ab',['agentA'], [('crawl',f'url-{i}') for i in range(0,20,2)])
        events=[{'source':'crawl','slot':f'url-{i}','scores':{'agentA':1}} for i in range(0,20,2)]
        self.assertIn('agentA',evaluate(incomplete,commitment(incomplete),events,lambdas=(.8,)).first_crossings)

if __name__=='__main__':unittest.main()

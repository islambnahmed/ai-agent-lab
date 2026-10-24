import itertools
import math
import unittest
from opportunity_gate import OpportunityGate

class OpportunityGateTests(unittest.TestCase):
    def test_complete_opportunity_penalizes_missing(self):
        g=OpportunityGate(['a','b']);g.observe(1,{'a':1})
        self.assertEqual(g.missing_counts, {'a':0,'b':1})
        self.assertLess(g.log_e('b'),0)

    def test_explicit_none_equals_absence(self):
        a=OpportunityGate(['a']);b=OpportunityGate(['a'])
        a.observe(1,{});b.observe(1,{'a':None})
        self.assertEqual(a.snapshot(),b.snapshot())

    def test_sequential_rounds_only(self):
        g=OpportunityGate(['a']);g.observe(1,{'a':1})
        for t in (1,3,0):
            with self.assertRaises(ValueError):g.observe(t,{'a':1})
        self.assertEqual(g.round,1)

    def test_reject_invalid_atomic(self):
        g=OpportunityGate(['a','b'])
        for scores in ({'a':1,'b':float('nan')},{'a':True},{'x':1},{'a':1.1},[]):
            with self.assertRaises(ValueError):g.observe(1,scores)
            self.assertEqual(g.round,0)
        self.assertEqual(g.missing_counts['b'],0)

    def test_reject_bad_config(self):
        for names in ([],['a','a'],['a',''],['a',1]):
            with self.assertRaises(ValueError):OpportunityGate(names)
        for kw in ({'alpha':1},{'alpha':True},{'lambdas':(1,)},{'lambdas':()}):
            with self.assertRaises(ValueError):OpportunityGate(['a'],**kw)

    def test_full_observation_matches_standard_bet(self):
        g=OpportunityGate(['a'],lambdas=(.8,))
        for t,x in enumerate([1,-1,1,1,-1],1):g.observe(t,{'a':x})
        self.assertAlmostEqual(math.exp(g.log_e('a')),math.prod(1+.8*x for x in [1,-1,1,1,-1]))

    def test_exact_e_mean_le_one_under_adaptive_censoring(self):
        # Four different deterministic outcome-dependent observation policies.
        n=8
        for rule in ('all','only_positive','only_negative','alternating'):
            total=0.
            for signs in itertools.product((-1,1),repeat=n):
                g=OpportunityGate(['a'],lambdas=(.8,))
                for t,x in enumerate(signs,1):
                    observed = rule=='all' or (rule=='only_positive' and x>0) or (rule=='only_negative' and x<0) or (rule=='alternating' and t%2==1)
                    g.observe(t,{'a':x} if observed else {})
                total += math.exp(g.log_e('a'))
            self.assertLessEqual(total/2**n,1+1e-12,rule)

    def test_exact_fwer_two_agents_outcome_dependent_missing(self):
        # Enumerate 2^12 possible fair independent signs; hide every loss.
        n=6;hits=0;alpha=.2
        for signs in itertools.product((-1,1),repeat=2*n):
            g=OpportunityGate(['a','b'],alpha=alpha,lambdas=(.8,))
            for t in range(n):
                scores={}
                if signs[t]>0:scores['a']=1
                if signs[t+n]>0:scores['b']=1
                g.observe(t+1,scores)
            hits += bool(g.crossings)
        self.assertLessEqual(hits/2**(2*n),alpha)

    def test_counterexample_zero_imputation(self):
        # Fair alternating gains, but zero-imputation drops all negatives.
        g=OpportunityGate(['a'],lambdas=(.8,))
        naive=1.
        for t in range(1,61):
            x=1 if t%2 else -1
            g.observe(t,{'a':x} if x>0 else {})
            naive *= (1+.8*(x if x>0 else 0))
        self.assertFalse(g.crossings)
        self.assertGreaterEqual(naive,20)

    def test_untrusted_opportunity_enumerator_counterexample(self):
        # The guard cannot detect omitted entire opportunities if a caller
        # renumbers the surviving rounds. A trusted independent ledger is needed.
        g=OpportunityGate(['a'])
        source=[1 if t%2 else -1 for t in range(1,121)]
        kept=[x for x in source if x>0]
        for t,x in enumerate(kept,1):g.observe(t,{'a':x})
        self.assertIn('a',g.crossings)
        self.assertEqual(g.missing_counts['a'],0)

    def test_positive_power_with_no_missing(self):
        g=OpportunityGate(['a'])
        for t in range(1,101):g.observe(t,{'a':1})
        self.assertIn('a',g.crossings)

if __name__=='__main__':unittest.main()

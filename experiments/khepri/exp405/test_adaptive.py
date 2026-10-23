import unittest
from adaptive_planner import *

class AdaptiveTests(unittest.TestCase):
    def setUp(self):
        self.tools = {
            'a':Tool('a','x',.99,.05,.2),
            'b':Tool('b','x',.995,.05,.2),
            'c':Tool('c','y',.82,.2,.7),
        }
        self.model = Model(.2,{'x':.02,'y':.1},{'x':.98,'y':.1})

    def test_worlds_sum_one(self):
        self.assertAlmostEqual(sum(w for w,_ in worlds(self.model)),1.)
    def test_same_domain_inference(self):
        pa, failb, pb=pair_stats(self.tools,self.model,'a','b')
        self.assertLess(failb/(1-pa),pb)
    def test_fallback_switches_to_independent_domain(self):
        result=adaptive_policy(self.tools,self.model,10,'a')
        self.assertEqual(result['fallback'],'c')
    def test_conditional_probability_identity(self):
        pa, failb, pb=pair_stats(self.tools,self.model,'a','b')
        self.assertAlmostEqual(pa+failb,static_utility(self.tools,self.model,1,('a','b'))+.4)
    def test_static_parallel_costs_both(self):
        x=static_utility(self.tools,self.model,10,('a','c'))
        pa,failb,_=pair_stats(self.tools,self.model,'a','c')
        self.assertAlmostEqual(x,10*(pa+failb)-.9)
    def test_adaptive_saves_fallback_cost_when_first_succeeds(self):
        result=adaptive_policy(self.tools,self.model,10,'a')
        self.assertGreater(result['utility'],static_utility(self.tools,self.model,10,('a','c')))
    def test_deadline_can_reverse_preference(self):
        fast=optimize(self.tools,self.model,10,1)
        slow=optimize(self.tools,self.model,10,.01)
        self.assertGreater(fast['gain'],slow['gain'])
        self.assertIsNone(adaptive_policy(self.tools,self.model,10,'a',.01)['fallback'])
    def test_never_retry_perfect_first(self):
        tools={'a':Tool('a','x',1,1,.2),'b':Tool('b','y',.9,.9,.1)}
        r=adaptive_policy(tools,self.model,10,'a')
        self.assertIsNone(r['fallback'])
        self.assertEqual(r['p_fallback_invoked'],0)
    def test_no_free_fallback_if_zero_reward(self):
        self.assertIsNone(adaptive_policy(self.tools,self.model,0,'a')['fallback'])
    def test_reject_duplicate_tool_names(self):
        with self.assertRaises(ValueError):static_utility(self.tools,self.model,10,('a','a'))
    def test_reject_unknown_tool(self):
        with self.assertRaises(ValueError):pair_stats(self.tools,self.model,'a','z')
    def test_reject_nan(self):
        with self.assertRaises(ValueError):optimize(self.tools,Model(float('nan'),self.model.calm,self.model.shocked),10)
    def test_reject_negative_cost(self):
        bad={**self.tools,'a':Tool('a','x',.9,.1,-1)}
        with self.assertRaises(ValueError):optimize(bad,self.model,10)
    def test_reject_bad_deadline(self):
        with self.assertRaises(ValueError):optimize(self.tools,self.model,10,1.1)
    def test_independent_domain_conditional_equals_marginal(self):
        model=Model(.3,{'x':.1,'y':.2},{'x':.1,'y':.2})
        pa,failc,pc=pair_stats(self.tools,model,'a','c')
        self.assertAlmostEqual(failc/(1-pa),pc)
    def test_shared_domain_correlation_is_not_independence(self):
        pa,failb,pb=pair_stats(self.tools,self.model,'a','b')
        self.assertGreater(abs(failb-(1-pa)*pb),.05)
    def test_static_can_win_when_deadline_tight(self):
        self.assertLess(optimize(self.tools,self.model,10,.1)['gain'],0)
    def test_monte_carlo_cross_check(self):
        from benchmark import simulate
        policy=adaptive_policy(self.tools,self.model,10,'a',.7)
        estimate=simulate(self.tools,self.model,10,'a',policy['fallback'],.7,40000,77)
        self.assertLess(abs(estimate-policy['utility']),.10)
    def test_no_repeated_second(self):
        r=adaptive_policy(self.tools,self.model,10,'b')
        self.assertNotEqual(r['fallback'],'b')

if __name__=='__main__':unittest.main()

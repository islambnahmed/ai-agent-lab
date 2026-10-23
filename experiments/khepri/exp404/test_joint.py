import unittest
from joint_planner import ShockModel, joint_success, independent_success, marginals, select, monte_carlo_joint
from planner import Tool, Plan, exact_success

class JointTests(unittest.TestCase):
    def setUp(self):
        self.tools = {'a': Tool('a','a',1,0,.1), 'b': Tool('b','b',1,0,.1),
                      'c': Tool('c','c',1,0,.1)}
        self.m = ShockModel(.2, {'a':0,'b':0,'c':.2}, {'a':1,'b':1,'c':.2})
        self.or_plan = Plan('or', (('a','b'),))
        self.and_plan = Plan('and', (('a',),('b',)))

    def test_marginal_outages(self):
        self.assertAlmostEqual(marginals(self.m)['a'],.2)
    def test_parallel_common_shock(self):
        self.assertAlmostEqual(joint_success(self.tools,self.m,self.or_plan),.8)
        self.assertAlmostEqual(independent_success(self.tools,self.m,self.or_plan),.96)
    def test_serial_common_shock(self):
        self.assertAlmostEqual(joint_success(self.tools,self.m,self.and_plan),.8)
        self.assertAlmostEqual(independent_success(self.tools,self.m,self.and_plan),.64)
    def test_identical_regimes(self):
        m = ShockModel(.42,{'a':.1,'b':.3,'c':.4},{'a':.1,'b':.3,'c':.4})
        self.assertAlmostEqual(joint_success(self.tools,m,self.or_plan),independent_success(self.tools,m,self.or_plan))
    def test_shock_zero(self):
        m = ShockModel(0,{'a':.1,'b':.3,'c':.4},{'a':.9,'b':.8,'c':.4})
        self.assertAlmostEqual(joint_success(self.tools,m,self.or_plan),exact_success(self.tools,m.calm,self.or_plan))
    def test_shock_one(self):
        m = ShockModel(1,{'a':.1,'b':.3,'c':.4},{'a':.9,'b':.8,'c':.4})
        self.assertAlmostEqual(joint_success(self.tools,m,self.or_plan),exact_success(self.tools,m.shocked,self.or_plan))
    def test_anticorrelation_reverses_or(self):
        m = ShockModel(.5,{'a':0,'b':1,'c':0},{'a':1,'b':0,'c':0})
        self.assertAlmostEqual(joint_success(self.tools,m,self.or_plan),1)
        self.assertAlmostEqual(independent_success(self.tools,m,self.or_plan),.75)
    def test_monte_carlo(self):
        self.assertLess(abs(monte_carlo_joint(self.tools,self.m,self.or_plan,20000,42)-.8),.02)
    def test_reject_bad_shock_probability(self):
        with self.assertRaises(ValueError): marginals(ShockModel(1.2,{'a':.2},{'a':.3}))
    def test_reject_missing_domain(self):
        with self.assertRaises(ValueError): marginals(ShockModel(.2,{'a':.2},{'b':.3}))
    def test_reject_nan(self):
        with self.assertRaises(ValueError): marginals(ShockModel(.2,{'a':float('nan')},{'a':.3}))
    def test_reject_duplicate_plan_names(self):
        with self.assertRaises(ValueError): select(self.tools,self.m,(self.or_plan,self.or_plan),10)
    def test_reject_unknown_method(self):
        with self.assertRaises(ValueError): select(self.tools,self.m,(self.or_plan,),10,'fake')
    def test_reject_invalid_reward(self):
        with self.assertRaises(ValueError): select(self.tools,self.m,(self.or_plan,),float('nan'))
    def test_reject_empty_plans(self):
        with self.assertRaises(ValueError): select(self.tools,self.m,(),10)
    def test_select_counterexample(self):
        t = {**self.tools, 'd': Tool('d','c',1,0,.5)}
        m = ShockModel(.2,{'a':0,'b':0,'c':.1},{'a':1,'b':1,'c':.1})
        plans = (self.or_plan, Plan('single',(('d',),)))
        self.assertEqual(select(t,m,plans,10,'joint')[0],'single')
        self.assertEqual(select(t,m,plans,10,'independent')[0],'or')

if __name__=='__main__': unittest.main()

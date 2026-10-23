import random
import unittest
from robust_planner import *


class RobustTests(unittest.TestCase):
    def setUp(self):
        self.tools = {'a':Tool('a','x',.99,.05,.25), 'b':Tool('b','x',.995,.05,.30),
                      'c':Tool('c','y',.86,.3,.70)}
        self.models = [Model(.05,{'x':.02,'y':.03},{'x':.95,'y':.2}),
                       Model(.60,{'x':.02,'y':.03},{'x':.95,'y':.2})]

    def test_world_normalization(self):
        for m in self.models:
            self.assertAlmostEqual(sum(w for w,_ in worlds(m)),1)

    def test_pair_identity(self):
        for m in self.models:
            pa,pfb,pf=pair_stats(self.tools,m,'a','c')
            self.assertAlmostEqual(pa+pf,1)
            self.assertGreaterEqual(pfb,0)
            self.assertLessEqual(pfb,pf)

    def test_parallel_symmetric(self):
        for m in self.models:
            self.assertAlmostEqual(utility(self.tools,m,10,.5,('parallel','a','c')),
                                   utility(self.tools,m,10,.5,('parallel','c','a')))

    def test_deadline_zero_adaptive_not_better_than_single(self):
        for m in self.models:
            self.assertLessEqual(utility(self.tools,m,10,0,('adaptive','a','c')),
                                 utility(self.tools,m,10,0,('single','a')))

    def test_adaptive_never_more_expensive_than_parallel_if_deadline_one(self):
        for m in self.models:
            self.assertGreaterEqual(utility(self.tools,m,10,1,('adaptive','a','c')),
                                    utility(self.tools,m,10,1,('parallel','a','c')))

    def test_robust_worst_at_least_nominal_worst(self):
        r=choose(self.tools,self.models,10,.8)
        self.assertGreaterEqual(r['robust_worst']+1e-10,r['nominal_worst'])

    def test_identical_models_same_optimum(self):
        r=choose(self.tools,[self.models[0],self.models[0]],10,.8)
        self.assertEqual(r['nominal'],r['robust'])

    def test_single_model_same_optimum(self):
        r=choose(self.tools,[self.models[0]],10,.8)
        self.assertEqual(r['nominal'],r['robust'])

    def test_skip_when_all_costs_exceed_reward(self):
        costly={n:Tool(t.name,t.domain,t.healthy,t.outage,100) for n,t in self.tools.items()}
        self.assertEqual(choose(costly,self.models,1,1)['robust'],('skip',))

    def test_reject_nan(self):
        with self.assertRaises(ValueError):choose(self.tools,[Model(float('nan'),self.models[0].calm,self.models[0].shocked)],10,.8)

    def test_reject_invalid_domain(self):
        with self.assertRaises(ValueError):choose(self.tools,[Model(.2,{'x':.1},{'x':.1})],10,.8)

    def test_reject_bad_cost(self):
        bad={**self.tools,'a':Tool('a','x',.99,.05,-.1)}
        with self.assertRaises(ValueError):choose(bad,self.models,10,.8)

    def test_monte_carlo_independent(self):
        rng=random.Random(406)
        m=self.models[1]; p=('adaptive','a','c'); reward=10; deadline=.7
        total=0; n=80000
        for _ in range(n):
            shock=rng.random()<m.shock
            rates=m.shocked if shock else m.calm
            down={d:rng.random()<rates[d] for d in sorted(rates)}
            a=self.tools['a']; b=self.tools['c']
            sa=rng.random()<(a.outage if down[a.domain] else a.healthy)
            payoff=-a.cost
            if sa:
                payoff+=reward
            else:
                payoff-=b.cost
                sb=rng.random()<(b.outage if down[b.domain] else b.healthy)
                if sb and rng.random()<deadline:payoff+=reward
            total+=payoff
        self.assertLess(abs(total/n-utility(self.tools,m,reward,deadline,p)),.08)

    def test_policy_count(self):
        self.assertEqual(len(policies(self.tools)),13)


if __name__=='__main__':unittest.main()

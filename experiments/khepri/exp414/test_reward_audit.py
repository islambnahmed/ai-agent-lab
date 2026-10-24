import math,random,unittest
from reward_audit import (Observation,censored_map,naive_rate,probability,select,
                          make_schedule,replay,sample_counts)
from benchmark import evaluate

class RewardAuditTests(unittest.TestCase):
    def test_censored_no_data_prior_mode(self):
        self.assertAlmostEqual(censored_map([]),.5)
    def test_censored_all_negative(self):
        self.assertAlmostEqual(censored_map([Observation(3,False),Observation(2,False)]),.5/6)
    def test_censored_positive_not_one_event(self):
        h=[Observation(3,True)]*50
        self.assertGreater(censored_map(h),naive_rate(h)*3)
    def test_select_reference(self):
        self.assertEqual(select([1,1,1],[0,0,0],[.5,.5,.5],2),(0,1))
    def test_prob_stability(self):
        self.assertAlmostEqual(probability(1e-12,1),1e-12)
        self.assertEqual(probability(1000,2),1)
    def test_binary_hit_equivalence(self):
        counts=[[0,2,0,1,0,0,1],[1,0,0,0,3,0,0],[0,0,0,0,0,0,0]]
        impacts=[5,2,4]
        for policy in ('censored','naive','oracle','round_robin','freshness_oracle'):
            sched=make_schedule(impacts,[.2,.3,.1],counts,policy,1)
            last=[-1]*len(impacts);expected=0
            for day,chosen in enumerate(sched):
                for i in chosen:
                    if sum(counts[i][last[i]+1:day+1])>0: expected+=impacts[i]
                    last[i]=day
            self.assertEqual(replay(impacts,counts,sched)['binary_hits'],expected)
    def test_exact_objective_reversal(self):
        counts=[[1]*6,[1]+[0]*5];impacts=[6,5]
        a=[(0,)]*6
        b=[(1,)]+[(0,)]*5
        ra=replay(impacts,counts,a);rb=replay(impacts,counts,b)
        self.assertGreater(ra['binary_hits'],rb['binary_hits'])
        self.assertGreater(ra['stale_days'],rb['stale_days'])
        self.assertGreater(ra['stale_days_after'],rb['stale_days_after'])
        self.assertEqual((ra['binary_hits'],rb['binary_hits']),(36,35))
        self.assertEqual((ra['stale_days'],rb['stale_days']),(66,41))
    def test_no_events(self):
        counts=[[0]*5 for _ in range(3)]
        for p in ('censored','naive','oracle','round_robin','freshness_oracle'):
            m=replay([2,3,4],counts,make_schedule([2,3,4],[.1,.2,.3],counts,p,2))
            self.assertEqual(m['binary_hits'],0)
            self.assertEqual(m['timely_events'],0)
            self.assertEqual(m['stale_days'],0)
    def test_all_checked_each_day(self):
        counts=[[1]*5 for _ in range(3)]
        sched=make_schedule([2,3,4],[.1,.2,.3],counts,'oracle',3)
        m=replay([2,3,4],counts,sched)
        self.assertEqual(m['binary_hits'],45)
        self.assertEqual(m['stale_days'],45)
        self.assertEqual(m['stale_days_after'],0)
        self.assertAlmostEqual(m['timely_events'],45)
    def test_zero_budget(self):
        counts=[[1]*4,[0]*4]
        m=replay([3,4],counts,make_schedule([3,4],[.2,.3],counts,'censored',0))
        self.assertEqual(m['binary_hits'],0)
        self.assertEqual(m['stale_days_after'],12)
    def test_latency_discount(self):
        counts=[[1,0,0]];sched=[(),(),(0,)]
        a=replay([3],counts,sched,tau=.5)['timely_events']
        b=replay([3],counts,sched,tau=5)['timely_events']
        self.assertLess(a,b)
        self.assertLess(b,3)
    def test_stale_ordering(self):
        rng=random.Random(414)
        counts=sample_counts([.1,.4,2],20,rng)
        for p in ('censored','naive','oracle','round_robin','freshness_oracle'):
            sched=make_schedule([4,3,2],[.1,.4,2],counts,p,1)
            m=replay([4,3,2],counts,sched)
            self.assertGreaterEqual(m['stale_days'],m['stale_days_after'])
    def test_deterministic_seed(self):
        self.assertEqual(evaluate(seed=1,reps=2,days=10),evaluate(seed=1,reps=2,days=10))
    def test_bad_budget(self):
        with self.assertRaises(ValueError):make_schedule([1],[.1],[[0]],'oracle',2)
    def test_bad_negative_counts(self):
        with self.assertRaises(ValueError):make_schedule([1],[.1],[[-1]],'oracle',1)
    def test_bad_replay_index(self):
        with self.assertRaises(ValueError):replay([1],[[1]],[(2,)])
    def test_bad_replay_tau(self):
        with self.assertRaises(ValueError):replay([1],[[1]],[(0,)],tau=0)
    def test_no_future_leakage(self):
        c1=[[0,1,0,0,1,0],[1,0,0,0,0,1]]
        c2=[[0,1,0,9,9,9],[1,0,0,9,9,9]]
        for p in ('censored','naive','oracle','round_robin','freshness_oracle'):
            a=make_schedule([3,2],[.2,.5],c1,p,1)
            b=make_schedule([3,2],[.2,.5],c2,p,1)
            self.assertEqual(a[:3],b[:3])

if __name__=='__main__':unittest.main()

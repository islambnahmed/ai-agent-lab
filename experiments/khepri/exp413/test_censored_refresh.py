import math, random, unittest
from censored_refresh import Observation, censored_map, naive_count_rate, probability, choose_refresh, run_policy

class CensoredRefreshTests(unittest.TestCase):
    def test_no_data_prior_mode(self):
        self.assertAlmostEqual(censored_map([]), .5)
    def test_all_negatives_exact_mode(self):
        self.assertAlmostEqual(censored_map([Observation(3,False),Observation(2,False)]), .5/6)
    def test_positive_interval_is_not_one_event(self):
        xs=[Observation(3,True)]*50
        self.assertGreater(censored_map(xs),naive_count_rate(xs)*3)
    def test_stable_extreme_exposure(self):
        self.assertTrue(math.isfinite(censored_map([Observation(1000000,True)]*10)))
    def test_permutation_invariance(self):
        xs=[Observation(1,True),Observation(7,False),Observation(5,True)]
        self.assertAlmostEqual(censored_map(xs),censored_map(xs[::-1]),places=12)
    def test_root_is_maximum(self):
        xs=[Observation(3,True),Observation(5,False),Observation(2,True)]
        r=censored_map(xs)
        def logposterior(lam):
            return .5*math.log(lam)-lam+sum(math.log(-math.expm1(-lam*x.exposure)) if x.changed else -lam*x.exposure for x in xs)
        self.assertGreater(logposterior(r),logposterior(r*.9))
        self.assertGreater(logposterior(r),logposterior(r*1.1))
    def test_probability_stability(self):
        self.assertAlmostEqual(probability(1e-12,1),1e-12)
        self.assertEqual(probability(1000,2),1)
    def test_invalid_inputs(self):
        for xs in ([Observation(0,True)],[Observation(True,False)],[Observation(2,1)]):
            with self.assertRaises(ValueError):censored_map(xs)
        with self.assertRaises(ValueError):censored_map([],shape=1)
    def test_budget_tie_determinism(self):
        self.assertEqual(choose_refresh([1,1,1],[0,0,0],[.5,.5,.5],2),(0,1))
    def test_zero_budget(self):
        latent=[[False]*3,[True]*3]
        self.assertEqual(run_policy([1,1],[.1,.1],latent,'censored',0)[0],0)
    def test_no_events(self):
        latent=[[False]*10 for _ in range(3)]
        for method in ('censored','naive','oracle'):
            self.assertEqual(run_policy([1,2,3],[.1,.2,.3],latent,method)[0],0)
    def test_full_budget_every_day(self):
        latent=[[True]*8 for _ in range(3)]
        for method in ('censored','naive','oracle'):
            self.assertEqual(run_policy([1,2,3],[.1,.2,.3],latent,method,3)[0],48)
    def test_reproducible(self):
        rng=random.Random(413)
        latent=[[rng.random()<.3 for _ in range(20)] for _ in range(3)]
        args=([2,3,4],[.1,.2,.3],latent,'censored')
        self.assertEqual(run_policy(*args),run_policy(*args))

if __name__=='__main__':unittest.main()

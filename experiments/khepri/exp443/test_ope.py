import math
import random
import unittest
from dataclasses import replace
from ope import SEO,GOLD,estimate,sample,run_benchmark,validate_support

class OfflinePolicyEvaluationTests(unittest.TestCase):
    def test_known_truth(self):
        self.assertAlmostEqual(SEO.true_value(),.5)
        self.assertAlmostEqual(GOLD.true_value(),.5)
    def test_support_rejects_zero_propensity(self):
        invalid=replace(SEO,logging_p1=(1.0,1.0))
        with self.assertRaisesRegex(ValueError,'positivity'):
            validate_support(invalid)
    def test_support_accepts_low_positive_probability(self):
        validate_support(replace(SEO,logging_p1=(.999,.999)))
    def test_all_methods_equal_with_all_actions_matched(self):
        d=replace(SEO,logging_p1=(1.,0.))
        rows=[(0,1,1.,1.),(1,0,0.,0.),(0,1,0.,1.),(1,0,1.,0.)]
        r=estimate(d,rows)
        for key in ('naive','ips','snips','dr'):
            self.assertAlmostEqual(r[key],.5)
    def test_ips_weights_are_context_specific(self):
        rows=[(0,1,1.,.8),(1,0,0.,.2),(0,0,0.,.8),(1,1,0.,.2)]
        r=estimate(SEO,rows)
        self.assertAlmostEqual(r['ips'],1/.8/4)
    def test_deterministic_seed(self):
        self.assertEqual(sample(SEO,50,random.Random(42)),sample(SEO,50,random.Random(42)))
    def test_held_out_fit(self):
        rows=sample(GOLD,200,random.Random(8))
        self.assertTrue(math.isfinite(estimate(GOLD,rows)['dr']))
    def test_benchmark_naive_bias_and_ips_correction_seo(self):
        b=run_benchmark(SEO,repeats=250,n=600)
        self.assertGreater(abs(b['summary']['naive']['bias']),.13)
        self.assertLess(abs(b['summary']['ips']['bias']),.03)
        self.assertLess(abs(b['summary']['dr']['bias']),.03)
    def test_benchmark_naive_bias_and_ips_correction_gold(self):
        b=run_benchmark(GOLD,repeats=250,n=600)
        self.assertGreater(abs(b['summary']['naive']['bias']),.35)
        self.assertLess(abs(b['summary']['ips']['bias']),.07)
        self.assertLess(abs(b['summary']['dr']['bias']),.07)
    def test_wrong_propensity_can_break_ips(self):
        rows=sample(SEO,100000,random.Random(91))
        correct=estimate(SEO,rows)['ips']
        wrong=estimate(SEO,rows,propensity_override=.5)['ips']
        self.assertLess(abs(correct-SEO.true_value()),.025)
        self.assertGreater(abs(wrong-SEO.true_value()),.17)
    def test_no_overlap_is_not_solved_by_more_data(self):
        bad=replace(SEO,logging_p1=(1.,1.))
        rows=sample(bad,10000,random.Random(11))
        with self.assertRaises(ValueError):
            estimate(bad,rows)
    def test_low_overlap_inflates_variance(self):
        bad=replace(SEO,logging_p1=(.99,.99))
        good=replace(SEO,logging_p1=(.5,.5))
        a=run_benchmark(bad,repeats=120,n=500)
        b=run_benchmark(good,repeats=120,n=500)
        self.assertGreater(a['summary']['ips']['rmse'],b['summary']['ips']['rmse'])
        self.assertLess(a['summary']['ess']['mean'],b['summary']['ess']['mean'])

if __name__=='__main__': unittest.main()

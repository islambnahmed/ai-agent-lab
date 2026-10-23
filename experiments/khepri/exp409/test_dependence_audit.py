import math
import random
import unittest
from dependence_audit import (
    audit_deltas, audit_backtest, lag1_correlation, autocorrelation,
    exact_ar1_variance_inflation, ar1_effective_n,
)


class DependenceAuditTests(unittest.TestCase):
    def test_ar1_white_noise_exact(self):
        self.assertEqual(exact_ar1_variance_inflation(20, 0.0), 1.0)

    def test_ar1_positive_inflation(self):
        self.assertGreater(exact_ar1_variance_inflation(20, .8), 5.0)

    def test_ar1_negative_reduces_variance(self):
        self.assertLess(exact_ar1_variance_inflation(20, -.5), 1.0)

    def test_ess_at_rho_zero(self):
        self.assertEqual(ar1_effective_n(20, 0.0), 20.0)

    def test_ess_high_dependence(self):
        self.assertAlmostEqual(ar1_effective_n(20, .8), 20/9)

    def test_ess_conservative_negative(self):
        self.assertEqual(ar1_effective_n(20, -.5), 20.0)

    def test_constant_has_no_estimated_correlation(self):
        self.assertIsNone(lag1_correlation([2.0]*20))
        self.assertIsNone(audit_deltas([2.0]*20)['lag1_autocorrelation'])

    def test_finite_validation(self):
        for x in ([1,2], [1,2,float('nan')], [1,2,float('inf')]):
            with self.assertRaises(ValueError): audit_deltas(x)

    def test_lag_validation(self):
        for k in (-1,3,1.5):
            with self.assertRaises(ValueError): audit_deltas([1,2,3], hac_lags=k)

    def test_alternating_negative_autocorrelation(self):
        self.assertLess(lag1_correlation([1,-1]*20), -.9)

    def test_positive_autocorrelation(self):
        rng=random.Random(4); x=0; a=[]
        for _ in range(1000):
            x=.9*x+math.sqrt(1-.9**2)*rng.gauss(0,1)
            a.append(x)
        self.assertGreater(lag1_correlation(a), .7)
        out=audit_deltas(a)
        self.assertGreater(out['hac_se'],out['naive_se'])

    def test_backtest_adapter(self):
        result={'status':'evaluation_ready','results':[
            {'baseline_abs_error':b,'candidate_abs_error':c}
            for b,c in [(3,1),(2,1),(1,2),(3,1)]
        ]}
        self.assertEqual(audit_backtest(result)['mean_paired_improvement'],1.0)

    def test_no_holdout(self):
        with self.assertRaises(ValueError):
            audit_backtest({'status':'insufficient_holdout','results':[]})

    def test_seven_step_periodicity_not_detected_by_lag1_alone(self):
        values=[10.0 if i % 7 == 0 else 0.0 for i in range(140)]
        a=audit_deltas(values)
        self.assertLess(abs(a['lag1_autocorrelation']), .3)
        self.assertGreater(a['autocorrelation_lags_1_to_10'][7], .9)
        self.assertTrue(a['strong_higher_lag_structure_heuristic'])

    def test_autocorrelation_lag_validation(self):
        with self.assertRaises(ValueError): autocorrelation([1,2,3],3)

    def test_no_false_significance_claim(self):
        self.assertIn('not validated p-values',audit_deltas([1,2,3,4])['warning'])

if __name__ == '__main__': unittest.main()

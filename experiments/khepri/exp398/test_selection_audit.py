import unittest
from random import Random
from selection_audit import Row, scores, estimate, select_threshold, evaluate_fixed_policy
from benchmark import sample, true_value, THRESHOLDS, run_trial


class TestSelectionAudit(unittest.TestCase):
    def test_complete_labels_match_true_reward(self):
        rows=[Row(.8,True,1),Row(.4,False,1),Row(.2,True,1)]
        self.assertAlmostEqual(estimate(rows,.3),(1-2-.15)/3)
    def test_zero_propensity_counterfactual_rejected(self):
        with self.assertRaises(ValueError): estimate([Row(.6,None,0)],.5)
    def test_zero_propensity_below_threshold_allowed(self):
        self.assertAlmostEqual(estimate([Row(.6,None,0)],.7),-.15)
    def test_no_outcome_fabrication(self):
        self.assertAlmostEqual(estimate([Row(.6,None,.2)],.5),-.15)
    def test_known_inverse_propensity(self):
        self.assertAlmostEqual(estimate([Row(.6,True,.25)],.5),-.15+(1+.15)/.25)
    def test_invalid_propensity(self):
        with self.assertRaises(ValueError): estimate([Row(.6,None,1.1)],.5)
    def test_invalid_label(self):
        with self.assertRaises(ValueError): estimate([Row(.6,1,.2)],.5)
    def test_invalid_threshold(self):
        with self.assertRaises(ValueError): estimate([Row(.6,True,1)],float('nan'))
    def test_empty_rows(self):
        with self.assertRaises(ValueError): estimate([],.5)
    def test_empty_grid(self):
        with self.assertRaises(ValueError): select_threshold([Row(.5,True,1),Row(.6,False,1)],[])
    def test_negative_penalty(self):
        with self.assertRaises(ValueError): select_threshold([Row(.5,True,1),Row(.6,False,1)],[.5],-1)
    def test_single_row_se_fails(self):
        with self.assertRaises(ValueError): evaluate_fixed_policy([Row(.5,True,1)],.5)
    def test_complete_labels_threshold_selection(self):
        rows=[Row(.4,False,1),Row(.6,False,1),Row(.8,True,1),Row(.9,True,1)]
        self.assertEqual(select_threshold(rows,[.3,.5,.7,.95])['threshold'],.7)
    def test_randomized_audit_fixed_threshold_unbiased_in_expectation(self):
        rng=Random(9123); errors=[]
        for _ in range(200):
            rows,latent=sample(rng,'gold',1200,.1)
            errors.append(estimate(rows,.60)-true_value(latent,.60))
        self.assertLess(abs(sum(errors)/len(errors)),.025)
    def test_holdout_is_independent_under_no_shift(self):
        rng=Random(123)
        errors=[run_trial(rng,'seo',.10,0)['holdout_error'] for _ in range(100)]
        self.assertLess(abs(sum(errors)/len(errors)),.04)
    def test_drift_breaks_deployment_calibration(self):
        rng=Random(123)
        gaps=[run_trial(rng,'gold',.10,.20)['holdout_vs_deploy_gap'] for _ in range(100)]
        self.assertGreater(sum(gaps)/len(gaps),.04)

if __name__=='__main__': unittest.main()

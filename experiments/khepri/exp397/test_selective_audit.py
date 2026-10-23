import unittest
from selective_audit import Record, selective_accuracy, audit_accuracy, policy_value

class TestSelectiveAudit(unittest.TestCase):
    def test_complete_labels_exact(self):
        rows=[Record(.9,True,True,1),Record(.3,False,False,1),Record(.6,False,True,1)]
        self.assertAlmostEqual(audit_accuracy(rows),2/3)
        self.assertAlmostEqual(policy_value(rows,.5),(1 + 1 - .15)/3) # two accepted
    def test_selective_accuracy_is_not_population_accuracy(self):
        rows=[Record(.95,True,True,1),Record(.2,False,False,1),Record(.3,False,False,1)]
        self.assertEqual(selective_accuracy(rows),1)
        self.assertAlmostEqual(audit_accuracy(rows),1/3)
    def test_no_audit_unidentifiable(self):
        rows=[Record(.9,True,True,1),Record(.4,False,None,0)]
        with self.assertRaises(ValueError): audit_accuracy(rows)
        with self.assertRaises(ValueError): policy_value(rows,.3)
        self.assertAlmostEqual(policy_value(rows,.8),(1-.15)/2)
    def test_randomized_audit_inclusion_weights(self):
        rows=[Record(.9,True,True,1),Record(.4,False,False,.25),Record(.3,False,None,.25)]
        self.assertAlmostEqual(audit_accuracy(rows),1/3)
        self.assertAlmostEqual(policy_value(rows,.5),(1-.15-.15)/3)
    def test_full_audit_policy_exact(self):
        rows=[Record(.9,True,True,1),Record(.4,False,False,1),Record(.3,False,True,1)]
        self.assertAlmostEqual(policy_value(rows,.4),(.85-1.85-.15)/3)
    def test_no_accepted(self):
        self.assertIsNone(selective_accuracy([Record(.1,False,None,.2)]))
    def test_empty_rejected(self):
        with self.assertRaises(ValueError): selective_accuracy([])
    def test_bad_prob_rejected(self):
        with self.assertRaises(ValueError): audit_accuracy([Record(.1,False,None,1.1)])
    def test_missing_accepted_label_rejected(self):
        with self.assertRaises(ValueError): selective_accuracy([Record(.9,True,None,1)])
    def test_nonboolean_label_rejected(self):
        with self.assertRaises(ValueError): audit_accuracy([Record(.1,False,1,.5)])
    def test_policy_threshold_rejected(self):
        with self.assertRaises(ValueError): policy_value([Record(.9,True,True,1)],1.5)
    def test_zero_audit_policy_with_no_alt_accept_supported(self):
        rows=[Record(.9,True,True,1),Record(.4,False,None,0)]
        self.assertAlmostEqual(policy_value(rows,.95),-.15)

if __name__=='__main__': unittest.main()

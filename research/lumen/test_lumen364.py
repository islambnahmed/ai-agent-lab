import copy
import math
import random
import unittest
from lumen364 import audit
from lumen363 import InvalidEvidence


def base():
    return {'entities':['A','B','C'],
            'reports':[{'name':'a','members':['A'],'kind':'count','value':0},
                       {'name':'bc','members':['B','C'],'kind':'count','value':0}],
            'uncertain_groups':['bc'],'max_error_rate':0.2,
            'max_radius':1,'max_membership_changes':1,'max_corrupt_values':0}

class Tests(unittest.TestCase):
    def test_cardinality_false_accept(self):
        x=audit(base())
        fixed=next(r for r in x['scenarios'] if r['radius']==0 and r['preserve_group_size'])
        flexible=next(r for r in x['scenarios'] if r['radius']==1 and not r['preserve_group_size'])
        self.assertEqual((fixed['min_errors'],fixed['max_errors']),(0,0))
        self.assertEqual((flexible['min_errors'],flexible['max_errors']),(0,1))
        self.assertEqual(fixed['decision'],'accept_within_assumptions')
        self.assertEqual(flexible['decision'],'abstain')
        self.assertEqual(x['overall_decision'],'abstain')
        self.assertEqual(len(flexible['upper_witness']['membership']['bc']),1)
        self.assertEqual(sum(flexible['upper_witness']['outcomes'].values()),1)
        self.assertEqual(flexible['upper_witness']['outcomes'][flexible['upper_witness']['membership']['bc'][0]],0)
    def test_zero_radius_same_size(self):
        x=base(); x['max_radius']=0
        rows=audit(x)['scenarios']
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['min_errors'],rows[1]['min_errors'])
        self.assertEqual(rows[0]['max_errors'],rows[1]['max_errors'])
    def test_relaxed_cardinality_monotonicity(self):
        rng=random.Random(364)
        for _ in range(120):
            n=rng.randint(2,4); entities=list('ABCD'[:n])
            reports=[]
            for i in range(rng.randint(1,3)):
                members=[e for e in entities if rng.random()<0.65] or [entities[0]]
                kind=rng.choice(['count','or'])
                value=rng.randrange(len(members)+1) if kind=='count' else rng.randrange(2)
                reports.append({'name':str(i),'members':members,'kind':kind,'value':value})
            x={'entities':entities,'reports':reports,'uncertain_groups':[r['name'] for r in reports],
               'max_error_rate':0.5,'max_radius':2,'max_membership_changes':1,'max_corrupt_values':1}
            rows=audit(x)['scenarios']
            for d in range(3):
                same,free=rows[2*d:2*d+2]
                if same['status']=='solved':
                    self.assertEqual(free['status'],'solved')
                    self.assertLessEqual(free['min_errors'],same['min_errors'])
                    self.assertGreaterEqual(free['max_errors'],same['max_errors'])
            for preserve in (True,False):
                previous=None
                for row in rows:
                    if row['preserve_group_size'] != preserve or row['status'] != 'solved':continue
                    if previous is not None:
                        self.assertLessEqual(row['min_errors'],previous['min_errors'])
                        self.assertGreaterEqual(row['max_errors'],previous['max_errors'])
                    previous=row
    def test_reject_when_lower_above_threshold(self):
        x={'entities':['A'], 'reports':[{'name':'x','members':['A'],'kind':'count','value':1}],
           'uncertain_groups':[],'max_error_rate':0.5}
        self.assertEqual(audit(x)['overall_decision'],'reject_within_assumptions')
    def test_accept_equality(self):
        x={'entities':['A','B'], 'reports':[{'name':'x','members':['A','B'],'kind':'count','value':1}],
           'uncertain_groups':[],'max_error_rate':0.5}
        self.assertEqual(audit(x)['overall_decision'],'accept_within_assumptions')
    def test_no_reports_abstain(self):
        x={'entities':['A','B'],'reports':[],'uncertain_groups':[],'max_error_rate':0.5}
        self.assertEqual(audit(x)['overall_decision'],'abstain')
    def test_fail_closed_work_budget(self):
        x=base(); x['max_work']=1
        self.assertEqual(audit(x)['overall_decision'],'abstain')
        self.assertTrue(all(r['status']=='resource_limited' for r in audit(x)['scenarios']))
    def test_invalid_threshold(self):
        for bad in (True, None, float('nan'),float('inf'),-0.1,1.01,'0.2'):
            x=base();x['max_error_rate']=bad
            with self.assertRaises(InvalidEvidence):audit(x)
    def test_invalid_structure(self):
        for key,bad in [('entities','A'),('reports',{}),('uncertain_groups','bc')]:
            x=base();x[key]=bad
            with self.assertRaises(InvalidEvidence):audit(x)
    def test_infeasible_abstain(self):
        x={'entities':['A'], 'reports':[{'name':'x','members':['A'],'kind':'count','value':0},
             {'name':'y','members':['A'],'kind':'count','value':1}],
           'uncertain_groups':[],'max_error_rate':0.5}
        result=audit(x)
        self.assertEqual(result['overall_decision'],'abstain')
        self.assertTrue(all(r['status']=='infeasible' for r in result['scenarios']))
    def test_malformed_ids_fail_closed(self):
        for key,bad in [('entities',['A',{}]),('uncertain_groups',[{}])]:
            x=base();x[key]=bad
            with self.assertRaises(InvalidEvidence):audit(x)
        x=base();x['reports'][0]['members']=[{}]
        with self.assertRaises(InvalidEvidence):audit(x)
    def test_invalid_resource_caps(self):
        for key,bad in [('max_radius',True),('max_options',0),('max_work',-1)]:
            x=base();x[key]=bad
            with self.assertRaises(InvalidEvidence):audit(x)

if __name__=='__main__':unittest.main()

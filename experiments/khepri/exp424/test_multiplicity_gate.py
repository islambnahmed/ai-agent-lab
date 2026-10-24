import itertools
import math
import unittest
from multiplicity_gate import FamilywiseGate

class GateTests(unittest.TestCase):
    def test_fixed_weights_and_slots(self):
        g=FamilywiseGate(slots=4)
        self.assertEqual([g.register(str(i)) for i in range(4)], [.25]*4)
        with self.assertRaises(ValueError): g.register('overflow')

    def test_online_weights(self):
        g=FamilywiseGate(mode='online')
        weights=[g.register(str(i)) for i in range(12)]
        self.assertAlmostEqual(sum(weights), 1-2**(-12))

    def test_positive_evidence_crosses(self):
        g=FamilywiseGate(slots=1);g.register('x')
        for t in range(1,101):g.observe(t,{'x':1})
        self.assertIn('x',g.crossings)

    def test_negative_never_crosses(self):
        g=FamilywiseGate(slots=1);g.register('x')
        for t in range(1,101):g.observe(t,{'x':-1})
        self.assertNotIn('x',g.crossings)

    def test_invalid_atomic(self):
        g=FamilywiseGate(slots=2);g.register('x');g.register('y')
        with self.assertRaises(ValueError):g.observe(1,{'x':1,'y':float('nan')})
        self.assertEqual(g.last_round,0)
        self.assertEqual(g.snapshot()['x']['n'],0)

    def test_no_repeated_round(self):
        g=FamilywiseGate(slots=1);g.register('x');g.observe(2,{'x':0})
        with self.assertRaises(ValueError):g.observe(2,{'x':1})
        with self.assertRaises(ValueError):g.observe(1,{'x':1})

    def test_reject_bool_and_nonfinite(self):
        g=FamilywiseGate(slots=1);g.register('x')
        for v in (True,float('inf'),float('-inf'),1.001,-1.001):
            with self.assertRaises(ValueError):g.observe(1,{'x':v})

    def test_register_only_future(self):
        g=FamilywiseGate(mode='online');g.register('old')
        g.observe(1,{'old':1});g.register('new')
        self.assertEqual(g.snapshot()['new']['n'],0)
        g.observe(2,{'old':1,'new':-1})
        self.assertEqual(g.snapshot()['new']['n'],1)

    def test_reject_bad_configuration(self):
        for kwargs in ({'slots':0},{'slots':True},{'alpha':1,'slots':2},
                       {'alpha':float('nan'),'slots':2},{'mode':'online','slots':2},
                       {'slots':2,'lambdas':(1,)},{'slots':2,'lambdas':()}):
            with self.assertRaises(ValueError):FamilywiseGate(**kwargs)

    def test_duplicate_registration(self):
        g=FamilywiseGate(slots=2);g.register('x')
        with self.assertRaises(ValueError):g.register('x')

    def test_log_mixture_finite_long_run(self):
        g=FamilywiseGate(slots=1);g.register('x')
        for t in range(1,1001):g.observe(t,{'x':1 if t%2 else -1})
        self.assertTrue(math.isfinite(g.snapshot()['x']['log_e']))

    def test_exact_null_e_mean_one(self):
        for n in range(1,9):
            values=[]
            for signs in itertools.product((-1,1),repeat=n):
                g=FamilywiseGate(slots=1);g.register('x')
                for t,x in enumerate(signs,1):g.observe(t,{'x':x})
                values.append(math.exp(g.snapshot()['x']['log_e']))
            self.assertAlmostEqual(math.fsum(values)/len(values),1.,places=11)

    def test_exact_fwer_two_independent(self):
        alpha=.2;n=6;errors=0;total=0
        for signs in itertools.product((-1,1),repeat=2*n):
            g=FamilywiseGate(alpha=alpha,slots=2,lambdas=(.8,))
            g.register('a');g.register('b')
            for t in range(n):g.observe(t+1,{'a':signs[t],'b':signs[t+n]})
            errors+=bool(g.crossings);total+=1
        self.assertLessEqual(errors/total,alpha)

    def test_exact_fwer_shared_sign(self):
        alpha=.2;n=10;errors=0
        for signs in itertools.product((-1,1),repeat=n):
            g=FamilywiseGate(alpha=alpha,slots=2,lambdas=(.8,))
            g.register('a');g.register('b')
            for t,x in enumerate(signs,1):g.observe(t,{'a':x,'b':x})
            errors+=bool(g.crossings)
        self.assertLessEqual(errors/2**n,alpha)

    def test_selective_logging_counterexample(self):
        g=FamilywiseGate(slots=1);g.register('x')
        for t in range(1,61):g.observe(t,{'x':1} if t%2 else {})
        self.assertIn('x',g.crossings)

if __name__=='__main__':unittest.main()

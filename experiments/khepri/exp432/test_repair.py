import random
import unittest
from source_benchmark import random_instance
from planner import Task, Planner
from repair import fill, optimize, drop_and_repair, better

class RepairTests(unittest.TestCase):
    def test_greedy_counterexample_fixed(self):
        p=Planner([Task('a',3,frozenset({'x'})),Task('b',2,frozenset({'y'})),Task('c',2,frozenset({'z'}))],{'x':10,'y':6,'z':6},4)
        self.assertEqual(p.greedy(marginal=True).value,10)
        self.assertEqual(optimize(p).value,12)
    def test_dependent_removed_with_prerequisite(self):
        p=Planner([Task('setup',1,frozenset()),Task('deep',3,frozenset({'x'}),('setup',)),Task('other',2,frozenset({'y'}))],{'x':8,'y':4},4)
        current=p.plan(['setup','deep'])
        fixed=drop_and_repair(p,current,('setup',))
        self.assertEqual(fixed.tasks,('other',))
        self.assertEqual(fixed.value,4)
    def test_nonselected_drop_rejected(self):
        p=Planner([Task('a',1,frozenset({'x'})),Task('b',1,frozenset({'y'}))],{'x':1,'y':2},1)
        with self.assertRaises(ValueError): drop_and_repair(p,p.plan(['a']),('b',))
    def test_seed_must_include_prerequisites(self):
        p=Planner([Task('a',1,frozenset()),Task('b',2,frozenset({'x'}),('a',))],{'x':10},3)
        with self.assertRaises(ValueError): fill(p,['b'])
        self.assertEqual(fill(p,['a','b']).value,10)
    def test_zero_budget(self):
        p=Planner([Task('a',1,frozenset({'x'}))],{'x':10},0)
        self.assertEqual(optimize(p,seeded=True,max_drop=2).tasks,())
    def test_tie_prefers_lower_cost(self):
        p=Planner([Task('a',2,frozenset({'x'})),Task('b',1,frozenset({'x'}))],{'x':3},2)
        self.assertEqual(optimize(p).tasks,('b',))
    def test_bad_parameters(self):
        p=Planner([Task('a',1,frozenset({'x'}))],{'x':1},1)
        for k in (0,3):
            with self.assertRaises(ValueError): optimize(p,max_drop=k)
        with self.assertRaises(ValueError): optimize(p,max_rounds=-1)
    def test_random_invariants_and_monotonicity(self):
        rng=random.Random(432)
        for trial in range(300):
            n=rng.randint(3,10)
            risks={f'r{i}':rng.randint(0,20) for i in range(7)}
            tasks=[]
            for i in range(n):
                deps=tuple(f't{j}' for j in range(i) if rng.random()<.14)
                tasks.append(Task(f't{i}',rng.randint(1,7),frozenset(k for k in risks if rng.random()<.32),deps))
            p=Planner(tasks,risks,rng.randint(0,20))
            greedy=p.greedy(marginal=True)
            exact=p.exact()
            variants=[optimize(p,max_drop=1),optimize(p,max_drop=1,seeded=True),optimize(p,max_drop=2,seeded=True)]
            for plan in variants:
                self.assertLessEqual(plan.cost,p.budget)
                self.assertGreaterEqual(plan.value+1e-9,greedy.value)
                self.assertLessEqual(plan.value,exact.value+1e-9)
                self.assertEqual(p.plan(plan.tasks),plan)
                seen=set()
                for name in plan.tasks:
                    self.assertTrue(set(p.tasks[name].requires)<=seen)
                    seen.add(name)
    def test_known_local_optima_counterexamples(self):
        for domain, seed, gap in [('seo',432177,1),('gold',532441,3)]:
            p=random_instance(domain,seed)
            result=optimize(p,max_drop=2,seeded=True)
            self.assertAlmostEqual(p.exact().value-result.value,gap)

    def test_idempotent_output(self):
        p=Planner([Task('a',3,frozenset({'x'})),Task('b',2,frozenset({'y'})),Task('c',2,frozenset({'z'}))],{'x':10,'y':6,'z':6},4)
        self.assertEqual(optimize(p,seeded=True,max_drop=2),optimize(p,seeded=True,max_drop=2))
    def test_comparator(self):
        p=Planner([Task('a',1,frozenset({'x'})),Task('b',2,frozenset({'x'}))],{'x':1},2)
        self.assertTrue(better(p.plan(['a']),p.plan(['b'])))
        self.assertFalse(better(p.plan(['b']),p.plan(['a'])))

if __name__=='__main__': unittest.main()

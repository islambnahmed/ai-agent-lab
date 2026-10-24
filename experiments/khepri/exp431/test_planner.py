import unittest
import random
from planner import Task, Planner

class PlannerTests(unittest.TestCase):
    def test_overlap_counterexample(self):
        p=Planner([Task('A',2,frozenset({'x','y'})),Task('B',2,frozenset({'x','y'})),Task('C',2,frozenset({'z'}))],{'x':5,'y':5,'z':9},4)
        self.assertEqual(p.greedy(marginal=False).value,10)
        self.assertEqual(p.greedy(marginal=True).value,19)
        self.assertEqual(p.exact().value,19)
    def test_prerequisite_bundle(self):
        p=Planner([Task('scan',2,frozenset()),Task('deep',3,frozenset({'bad'}),('scan',)),Task('other',3,frozenset({'small'}))],{'bad':10,'small':2},5)
        self.assertEqual(p.exact().tasks,('scan','deep'))
        self.assertEqual(p.greedy(marginal=True).tasks,('scan','deep'))
    def test_topological(self):
        p=Planner([Task('a',1,frozenset({'x'}),('z',)),Task('z',1,frozenset())],{'x':1},2)
        self.assertEqual(p.exact().tasks,('z','a'))
    def test_bad_inputs(self):
        with self.assertRaisesRegex(ValueError,'cyclic'):
            Planner([Task('a',1,frozenset(),('b',)),Task('b',1,frozenset(),('a',))],{'x':1},2)
        with self.assertRaisesRegex(ValueError,'unknown'):
            Planner([Task('a',1,frozenset({'oops'}))],{'x':1},2)
        with self.assertRaisesRegex(ValueError,'positive'):
            Planner([Task('a',0,frozenset())],{'x':1},2)
    def test_random_oracle_bounds_and_dependencies(self):
        rng=random.Random(431)
        for trial in range(300):
            n=rng.randint(3,10)
            risks={f'r{i}':rng.randint(1,20) for i in range(7)}
            tasks=[]
            for i in range(n):
                prereqs=tuple(f't{j}' for j in range(i) if rng.random()<.12)
                covers=frozenset(k for k in risks if rng.random()<.28)
                tasks.append(Task(f't{i}',rng.randint(1,6),covers,prereqs))
            p=Planner(tasks,risks,rng.randint(2,20))
            exact=p.exact()
            for strategy in (p.greedy(marginal=True),p.greedy(marginal=False)):
                self.assertLessEqual(strategy.cost,p.budget)
                self.assertLessEqual(strategy.value,exact.value+1e-9)
                seen=set()
                for name in strategy.tasks:
                    self.assertTrue(set(p.tasks[name].requires)<=seen)
                    seen.add(name)
    def test_greedy_not_globally_optimal(self):
        p=Planner([Task('a',3,frozenset({'x'})),Task('b',2,frozenset({'y'})),Task('c',2,frozenset({'z'}))],{'x':10,'y':6,'z':6},4)
        self.assertEqual(p.greedy(marginal=True).value,10)
        self.assertEqual(p.exact().value,12)
    def test_weight_misspecification_counterexample(self):
        p=Planner([Task('A',2,frozenset({'x'})),Task('B',2,frozenset({'y'}))],{'x':10,'y':2},2)
        predicted=p.exact()
        self.assertEqual(predicted.tasks,('A',))
        actual={'x':1,'y':20}
        self.assertEqual(sum(actual[m] for m in predicted.covered),1)
        self.assertEqual(Planner(p.tasks.values(),actual,2).exact().value,20)

    def test_plan_over_budget_rejected(self):
        p=Planner([Task('a',3,frozenset({'x'}))],{'x':1},2)
        with self.assertRaisesRegex(ValueError,'budget'):
            p.plan(['a'])

    def test_duplicate_names_rejected(self):
        with self.assertRaises(ValueError):
            Planner([Task('a',1,frozenset()),Task('a',2,frozenset())],{'x':1},2)
if __name__=='__main__': unittest.main()

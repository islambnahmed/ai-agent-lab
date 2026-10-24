import itertools, math, random, unittest
from planner import Item, plan, evaluate


def independent_brute(items,budget,horizon):
    choices=[]
    for mask in range(1<<len(items)):
        subset=tuple(items[i].id for i in range(len(items)) if mask>>i&1)
        if sum(x.cost for x in items if x.id in subset)<=budget:
            choices.append(subset)
    best=-1
    for seq in itertools.product(choices,repeat=horizon):
        ages={x.id:0 for x in items}
        value=0
        for day in seq:
            for x in items:
                if x.id in day:
                    value+=x.impact*(1-math.exp(-x.rate*(ages[x.id]+1)))
                    ages[x.id]=0
                else:
                    ages[x.id]+=1
        best=max(best,value)
    return best

class PlannerTests(unittest.TestCase):
    def test_known_myopic_counterexample(self):
        items=[Item('a',1,12,.01),Item('b',3,16,.3),Item('c',2,16,.3),Item('d',2,25,.7)]
        optimal=plan(items,4,4)
        greedy=plan(items,4,4,'myopic')
        self.assertEqual(optimal,(('c','d'),('c','d'),('a','b'),('c','d')))
        self.assertGreater(evaluate(items,4,optimal),evaluate(items,4,greedy)+2)

    def test_exhaustive_independent_oracle(self):
        rng=random.Random(412)
        for _ in range(150):
            n=rng.randint(1,4);t=rng.randint(1,3);budget=rng.randint(0,5)
            items=[Item(str(i),rng.randint(1,4),rng.uniform(1,30),rng.uniform(.02,1)) for i in range(n)]
            self.assertAlmostEqual(evaluate(items,budget,plan(items,budget,t)),
                                   independent_brute(items,budget,t),places=9)

    def test_order_invariance(self):
        xs=[Item('z',2,4,.2),Item('b',1,3,.1),Item('a',1,5,.3)]
        self.assertEqual(plan(xs,2,4),plan(xs[::-1],2,4))

    def test_horizon_zero(self):
        self.assertEqual(plan([Item('a',1,2,.1)],1,0),())

    def test_zero_budget(self):
        self.assertEqual(plan([Item('a',1,2,.1)],0,3),((),(),()))

    def test_zero_rates(self):
        self.assertEqual(evaluate([Item('a',1,2,0)],1,plan([Item('a',1,2,0)],1,3)),0)

    def test_initial_ages(self):
        xs=[Item('a',1,5,.1),Item('b',1,4,.3)]
        self.assertAlmostEqual(evaluate(xs,1,plan(xs,1,2,initial_ages=(9,0)),initial_ages=(9,0)),
                               max(evaluate(xs,1,s,initial_ages=(9,0)) for s in itertools.product([(),('a',),('b',)],repeat=2)))

    def test_budget_rejects_boolean(self):
        with self.assertRaises(ValueError):plan([],True,1)

    def test_duplicate_reject(self):
        with self.assertRaises(ValueError):plan([Item('a',1,2,.1)]*2,1,1)

    def test_negative_rate_reject(self):
        with self.assertRaises(ValueError):plan([Item('a',1,2,-.1)],1,1)

    def test_invalid_age_reject(self):
        with self.assertRaises(ValueError):plan([Item('a',1,2,.1)],1,1,initial_ages=(True,))

    def test_invalid_action_reject(self):
        with self.assertRaises(ValueError):evaluate([Item('a',2,2,.1)],1,[('a',)])

    def test_over_limit_reject(self):
        with self.assertRaises(ValueError):plan([Item(str(i),1,1,.1) for i in range(7)],1,1)

    def test_misspecified_lookahead_can_lose(self):
        true=[Item('page-0',1,24.39638330488636,.03),
              Item('page-1',3,9.286935033436011,.3),
              Item('page-2',1,17.536869230834874,.7),
              Item('page-3',3,3.7140041651279603,.03)]
        threshold=sum(x.impact for x in true)/len(true)
        wrong=[Item(x.id,x.cost,x.impact,x.rate*(.05 if x.impact>=threshold else 10.)) for x in true]
        long_plan=plan(wrong,4,5)
        short_plan=plan(wrong,4,5,'myopic')
        self.assertLess(evaluate(true,4,long_plan),evaluate(true,4,short_plan))

    def test_gold_transfer(self):
        feeds=[Item('spot',2,20,.6),Item('fx',1,10,.03),Item('rates',2,12,.2)]
        self.assertGreaterEqual(evaluate(feeds,2,plan(feeds,2,4)),evaluate(feeds,2,plan(feeds,2,4,'myopic')))

if __name__=='__main__':unittest.main()

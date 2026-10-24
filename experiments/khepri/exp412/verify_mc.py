"""Independent paired-event Monte Carlo for constructed counterexample."""
import json,math,random
from planner import Item,plan,evaluate

def run(trials=100000,seed=412):
    items=[Item('a',1,12,.01),Item('b',3,16,.3),Item('c',2,16,.3),Item('d',2,25,.7)]
    opt=plan(items,4,4)
    myo=plan(items,4,4,'myopic')
    rng=random.Random(seed)
    sums=[0.,0.,0.]
    sums_sq=0.
    for _ in range(trials):
        events=[[rng.random() < 1-math.exp(-x.rate) for x in items] for _ in range(4)]
        vals=[]
        for policy in (opt,myo):
            pending=[False]*len(items)
            score=0.
            for t,day in enumerate(policy):
                for i,x in enumerate(items):
                    pending[i] |= events[t][i]
                    if x.id in day:
                        if pending[i]:score+=x.impact
                        pending[i]=False
            vals.append(score)
        diff=vals[0]-vals[1]
        sums[0]+=vals[0];sums[1]+=vals[1];sums[2]+=diff;sums_sq+=diff*diff
    mean=sums[2]/trials
    se=math.sqrt(max(0.,sums_sq/trials-mean*mean)/trials)
    return {'trials':trials,'seed':seed,'optimal_expected_analytic':evaluate(items,4,opt),
            'myopic_expected_analytic':evaluate(items,4,myo),
            'optimal_mc':sums[0]/trials,'myopic_mc':sums[1]/trials,
            'difference_mc':mean,'difference_95pct_normal_CI':[mean-1.96*se,mean+1.96*se],
            'optimal_actions':opt,'myopic_actions':myo}
if __name__=='__main__':print(json.dumps(run(),indent=2))

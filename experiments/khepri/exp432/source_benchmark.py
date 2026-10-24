"""Deterministic synthetic planning benchmark; no real SEO or market data."""
import json
import random
from statistics import mean
from planner import Task, Planner

DOMAINS = {
    'seo': ('canonical', 'indexability', 'robots', 'render', 'schema', 'duplicate', 'redirect', 'sitemap'),
    'gold': ('stale_quote', 'fx_drift', 'timezone', 'feed_gap', 'duplicate_tick', 'outlier', 'spread', 'rounding'),
}

def example(domain):
    m=DOMAINS[domain]
    weights=dict(zip(m,[12,11,8,10,7,8,6,5] if domain=='seo' else [16,9,14,8,12,18,6,7]))
    tasks=[
        Task('inventory',1,frozenset()),
        Task('quick_scan',2,frozenset(m[:3])),
        Task('deep_probe',4,frozenset(m[2:6]),('inventory',)),
        Task('cross_check',3,frozenset(m[4:8])),
        Task('duplicate_scan',2,frozenset(m[:3])),
        Task('audit',4,frozenset(m[1:5]),('inventory',)),
        Task('edge_case',2,frozenset(m[6:8])),
    ]
    if domain=='gold':
        tasks=[Task('source_check',2,frozenset(m[:2])),
               Task('feed_replay',4,frozenset(m[:4]),('source_check',)),
               Task('fx_cross',3,frozenset(m[1:4])),
               Task('tick_integrity',3,frozenset(m[3:6])),
               Task('outlier_probe',2,frozenset(m[5:7])),
               Task('reconcile',4,frozenset(m[4:8]),('source_check',))]
    return Planner(tasks,weights,8)

def random_instance(domain, seed):
    rng=random.Random(seed)
    modes=DOMAINS[domain]
    weights={m:rng.randint(1,20) if domain=='seo' else rng.randint(1,30) for m in modes}
    tasks=[]
    for i in range(10):
        prereqs=tuple(f't{j}' for j in range(i) if rng.random() < (.12 if domain=='seo' else .05))
        covers=frozenset(m for m in modes if rng.random() < (.48 if domain=='seo' else .22))
        tasks.append(Task(f't{i}',rng.randint(1,7),covers,prereqs))
    return Planner(tasks,weights,rng.randint(6,19))

def summarize(plans):
    return {'mean_covered_value':round(mean(p.value for p in plans),4),
            'mean_cost':round(mean(p.cost for p in plans),4)}

def run(trials=500):
    output={'seed':431,'trials_per_domain':trials,'domains':{}}
    for j,domain in enumerate(DOMAINS):
        cases=[random_instance(domain,431000+j*100000+i) for i in range(trials)]
        exact=[p.exact() for p in cases]
        marginal=[p.greedy(marginal=True) for p in cases]
        static=[p.greedy(marginal=False) for p in cases]
        output['domains'][domain]={
            'example':{key:{'tasks':plan.tasks,'cost':plan.cost,'covered_value':plan.value}
                       for key,plan in [('exact',example(domain).exact()),('marginal',example(domain).greedy(marginal=True)),('static',example(domain).greedy(marginal=False))]},
            'exact':summarize(exact),'marginal':summarize(marginal),'static':summarize(static),
            'marginal_equal_optimum':sum(abs(a.value-b.value)<1e-9 for a,b in zip(marginal,exact)),
            'static_equal_optimum':sum(abs(a.value-b.value)<1e-9 for a,b in zip(static,exact)),
            'marginal_beats_static':sum(a.value>b.value+1e-9 for a,b in zip(marginal,static)),
            'static_beats_marginal':sum(b.value>a.value+1e-9 for a,b in zip(marginal,static)),
        }
    return output

if __name__=='__main__':
    print(json.dumps(run(),indent=2,sort_keys=True))

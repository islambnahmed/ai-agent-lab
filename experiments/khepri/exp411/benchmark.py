"""Seeded synthetic benchmark. No live crawling or provider calls."""
import json
import math
import random
from scheduler import Item, choose


def scenario(kind):
    if kind == 'seo':
        # Mix of frequently updated expensive category pages and low-change posts.
        return [Item(f'page-{i:02}', 1+(i*7)%5, 1+(i*11)%20,
                     [.02, .07, .20, .5][i%4], 0) for i in range(24)], 9
    if kind == 'feeds':
        return [Item(f'feed-{i:02}', 1+(i*5)%4, 3+(i*13)%18,
                     [.03, .10, .25, .60][i%4], 0) for i in range(12)], 5
    raise ValueError(kind)


def simulate(kind, policy, seed, days=90, misspecified=False):
    initial, budget = scenario(kind)
    rng = random.Random(seed)
    events = [[rng.random() < -math.expm1(-x.rate) for x in initial] for _ in range(days)]
    age = [0] * len(initial)
    pending = [False] * len(initial)
    total = 0.
    found = 0
    spent = 0
    for day in range(days):
        for i, x in enumerate(initial):
            age[i] += 1
            pending[i] |= events[day][i]
        view = []
        for i, x in enumerate(initial):
            rate = x.rate
            if misspecified:
                # Systematic ranking error: high-impact high-change pages are underestimated.
                rate = x.rate * (.05 if x.impact >= 12 else 10.)
            view.append(Item(x.id, x.cost, x.impact, rate, age[i]))
        ids = set(choose(view, budget, policy))
        for i, x in enumerate(initial):
            if x.id in ids:
                spent += x.cost
                if pending[i]:
                    found += 1
                    total += x.impact
                pending[i] = False
                age[i] = 0
    return dict(impact=total, discoveries=found, spent=spent)


def run():
    out = {'design': '90 days, 100 paired seeds, same exogenous change events per policy; synthetic independent Bernoulli daily change events',
           'cases': {}}
    for kind in ('seo', 'feeds'):
        summary = {}
        for policy, wrong in (('dp', False), ('ratio', False), ('oldest', False), ('dp', True)):
            label = 'dp_misspecified' if wrong else policy
            vals = [simulate(kind, policy, seed, misspecified=wrong) for seed in range(100)]
            summary[label] = {k: round(sum(v[k] for v in vals)/len(vals), 4) for k in ('impact','discoveries','spent')}
        baseline = [simulate(kind, 'dp', seed)['impact'] for seed in range(100)]
        summary['paired_dp_minus_ratio'] = {
            'mean_impact': round(sum(a-simulate(kind, 'ratio', seed)['impact'] for seed,a in enumerate(baseline))/100, 4),
            'wins': sum(a>simulate(kind, 'ratio', seed)['impact'] for seed,a in enumerate(baseline)),
            'ties': sum(a==simulate(kind, 'ratio', seed)['impact'] for seed,a in enumerate(baseline))
        }
        out['cases'][kind] = summary
    return out


if __name__ == '__main__': print(json.dumps(run(), indent=2))

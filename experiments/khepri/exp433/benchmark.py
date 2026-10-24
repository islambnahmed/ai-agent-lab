import json
import random
from robust import generate, sampled_weights


def run(cases=300, samples=12):
    result = {'cases_per_domain': cases, 'samples_per_distribution_per_case': samples,
              'objectives': ['nominal', 'maximin', 'minimax_regret'], 'domains': {}}
    for domain, base in [('seo', 433000), ('gold', 533000)]:
        scores = {obj: {'worst_regret': 0., 'nominal_utility': 0.,
                        'realized_regret': {shape: 0. for shape in ('uniform', 'low', 'high')}}
                  for obj in result['objectives']}
        strict = {'minimax_beats_nominal_worst': 0, 'nominal_beats_minimax_realized_uniform': 0}
        counterexamples = []
        for idx in range(cases):
            p = generate(base + idx, domain)
            chosen = {obj: p.choose(obj) for obj in scores}
            mid = {r: sum(p.intervals[r])/2 for r in p.risks}
            for obj, plan in chosen.items():
                scores[obj]['worst_regret'] += p.worst_regret(plan)
                scores[obj]['nominal_utility'] += p.utility(plan, mid)
            a = p.worst_regret(chosen['nominal'])
            b = p.worst_regret(chosen['minimax_regret'])
            if b < a - 1e-9:
                strict['minimax_beats_nominal_worst'] += 1
                if len(counterexamples) < 2:
                    counterexamples.append({'seed': base + idx, 'intervals': p.intervals,
                        'tasks': [{'name': t.name, 'cost': t.cost, 'covers': sorted(t.covers),
                                   'requires': list(t.requires)} for t in p.tasks.values()],
                        'budget': p.budget, 'nominal_tasks': sorted(chosen['nominal'][0]),
                        'minimax_tasks': sorted(chosen['minimax_regret'][0]),
                        'nominal_worst_regret': a, 'minimax_worst_regret': b})
            rng = random.Random(base + idx + 900000)
            realized_uniform = {obj: 0 for obj in scores}
            for shape in ('uniform', 'low', 'high'):
                for _ in range(samples):
                    weights = sampled_weights(p, rng, shape)
                    oracle = max(p.utility(q, weights) for q in p.plans)
                    for obj, plan in chosen.items():
                        regret = oracle - p.utility(plan, weights)
                        scores[obj]['realized_regret'][shape] += regret
                        if shape == 'uniform':
                            realized_uniform[obj] += regret
            if realized_uniform['nominal'] < realized_uniform['minimax_regret'] - 1e-9:
                strict['nominal_beats_minimax_realized_uniform'] += 1
        for obj in scores:
            scores[obj]['worst_regret'] = round(scores[obj]['worst_regret']/cases, 4)
            scores[obj]['nominal_utility'] = round(scores[obj]['nominal_utility']/cases, 4)
            scores[obj]['realized_regret'] = {shape: round(value/(cases*samples), 4)
                for shape, value in scores[obj]['realized_regret'].items()}
        result['domains'][domain] = {'scores': scores, 'strict_cases': strict,
                                     'counterexamples': counterexamples}
    return result


if __name__ == '__main__':
    print(json.dumps(run(), indent=2, sort_keys=True))

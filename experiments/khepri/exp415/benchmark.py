"""Reproducible synthetic benchmark: optional peeking and transfer."""
import json
import random
from anytime_eval import first_crossing, naive_first_crossing


def simulate(replicates=3000, n=200, seed=415):
    rng = random.Random(seed)
    summary = {}
    for label, p in [('null_iid', 0.5), ('beneficial_iid', 0.62)]:
        naive = anytime = 0
        fixed_naive = 0
        stops = []
        for _ in range(replicates):
            xs = [1 if rng.random() < p else -1 for _ in range(n)]
            t = first_crossing(xs)
            naive += naive_first_crossing(xs) is not None
            anytime += t is not None
            if t is not None: stops.append(t)
            fixed_naive += naive_first_crossing(xs, min_n=n, step=1) is not None
        summary[label] = dict(replicates=replicates, n=n, naive_peek_rate=naive/replicates,
            anytime_rate=anytime/replicates, fixed_horizon_naive_rate=fixed_naive/replicates,
            mean_anytime_stop=(sum(stops)/len(stops) if stops else None))
    # A second domain: paired binary tool outcomes (zeroes possible).
    for label, pa, pb in [('tool_equal', .6, .6), ('tool_better', .72, .52)]:
        count = 0
        for _ in range(replicates):
            xs = [(rng.random() < pa) - (rng.random() < pb) for _ in range(n)]
            count += first_crossing(xs) is not None
        summary[label] = dict(replicates=replicates, n=n, anytime_rate=count/replicates)
    # Counterexample: unconditional mean zero but conditional mean != 0.
    dependent = []
    for _ in range(replicates):
        latent = 1 if rng.random() < .5 else -1
        dependent.append(first_crossing([latent]*n) is not None)
    summary['latent_common_cause'] = dict(replicates=replicates, n=n,
        anytime_rate=sum(dependent)/replicates, warning='NOT a conditional-mean null')
    return summary

if __name__ == '__main__':
    result = simulate()
    print(json.dumps(result, indent=2))
    with open('results.json', 'w', encoding='utf8') as f:
        json.dump(result, f, indent=2)

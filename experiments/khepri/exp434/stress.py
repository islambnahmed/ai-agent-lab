"""Reproducible multi-seed and negative-control checks for PIT revision leakage."""
from dataclasses import replace
import json
import random
from statistics import mean
from pit_eval import (benchmark, synthetic_domain, feature_snapshot,
                      walk_forward_folds, score)


def evaluate(examples, revisions):
    folds = list(walk_forward_folds(examples))
    total = sum(len(test) for _, test in folds)
    out = {}
    for name, pit in [('strict', True), ('leaky', False)]:
        snapshots = feature_snapshot(examples, revisions, pit)
        out[name] = sum(score(train, test, snapshots)[0] for train, test in folds)/total
    return out


def negative_control(domain, seed=434):
    """Keep early features; replace post-decision revisions with independent coin flips."""
    ex, rev = synthetic_domain(domain, seed)
    rng = random.Random(seed + 90000)
    revisions = [replace(r, value=rng.randrange(2)) if r.revision == 2 else r for r in rev]
    return evaluate(ex, revisions)


def main():
    out = {}
    for domain in ('gold', 'seo'):
        samples = [benchmark(domain, seed=s) for s in range(434, 634)]
        diffs = [s['leaky_accuracy']-s['strict_accuracy'] for s in samples]
        control = [negative_control(domain, seed=s) for s in range(434, 634)]
        out[domain] = {
            'seeds': 200,
            'mean_strict_accuracy': round(mean(s['strict_accuracy'] for s in samples), 4),
            'mean_leaky_accuracy': round(mean(s['leaky_accuracy'] for s in samples), 4),
            'mean_leakage_inflation': round(mean(diffs), 4),
            'min_leakage_inflation': round(min(diffs), 4),
            'positive_inflation_cases': sum(d > 0 for d in diffs),
            'negative_control_mean_strict': round(mean(s['strict'] for s in control), 4),
            'negative_control_mean_leaky': round(mean(s['leaky'] for s in control), 4),
        }
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()

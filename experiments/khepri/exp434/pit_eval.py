"""Point-in-time feature revision evaluation for offline binary-agent decisions.
Standard library only; synthetic data; no external actions.
"""
from dataclasses import dataclass
from collections import defaultdict
import random


@dataclass(frozen=True)
class Example:
    key: str
    decision_at: int
    label: int
    label_ready_at: int


@dataclass(frozen=True)
class Revision:
    key: str
    observed_at: int
    available_at: int
    revision: int
    value: int


def feature_snapshot(examples, revisions, point_in_time=True):
    """Latest *available* revision per example, never using future observations.

    When point_in_time=False, deliberately simulates a leaky historical backfill.
    """
    grouped = defaultdict(list)
    for r in revisions:
        if r.value not in (0, 1):
            raise ValueError('feature values must be binary')
        grouped[r.key].append(r)
    if len({e.key for e in examples}) != len(examples):
        raise ValueError('duplicate example keys')
    result = {}
    for e in examples:
        candidates = [r for r in grouped[e.key]
                      if r.observed_at <= e.decision_at and
                      (not point_in_time or r.available_at <= e.decision_at)]
        if candidates:
            r = max(candidates, key=lambda r: (r.available_at, r.revision))
            result[e.key] = r
    return result


def walk_forward_folds(examples, min_train=80, test_size=40, gap=0):
    """Strictly chronological folds, with train labels matured by test start."""
    if min_train < 1 or test_size < 1 or gap < 0:
        raise ValueError('invalid fold parameters')
    ordered = sorted(examples, key=lambda e: (e.decision_at, e.key))
    if len({e.decision_at for e in ordered}) != len(ordered):
        raise ValueError('decision timestamps must be unique')
    for start in range(min_train, len(ordered), test_size):
        test = ordered[start:start + test_size]
        if len(test) < test_size:
            break
        cutoff = test[0].decision_at
        eligible = ordered[:max(0, start-gap)]
        train = [e for e in eligible if e.label_ready_at <= cutoff]
        if not train:
            continue
        assert max(e.decision_at for e in train) < cutoff
        assert all(e.label_ready_at <= cutoff for e in train)
        yield train, test


def fit_binary_stump(train, snapshots):
    """Fit a single binary feature with majority-class fallback; no tuning on test."""
    counts = [[0, 0], [0, 0]]
    prior = [0, 0]
    for e in train:
        prior[e.label] += 1
        if e.key in snapshots:
            counts[snapshots[e.key].value][e.label] += 1
    default = int(prior[1] > prior[0])
    choices = [int(row[1] > row[0]) if sum(row) else default for row in counts]
    return default, choices


def score(train, test, snapshots):
    default, choices = fit_binary_stump(train, snapshots)
    predictions = [choices[snapshots[e.key].value] if e.key in snapshots else default
                   for e in test]
    return sum(p == e.label for p, e in zip(predictions, test)), len(test)


def synthetic_domain(domain, seed=434):
    """Two different delays/prevalences; revised reports contain hindsight leakage."""
    settings = {
        'gold': dict(n=360, base=0.50, early_accuracy=0.56,
                     final_accuracy=0.985, feature_delay=1, label_delay=2),
        'seo': dict(n=360, base=0.38, early_accuracy=0.61,
                    final_accuracy=0.97, feature_delay=7, label_delay=14),
    }
    if domain not in settings:
        raise ValueError('unknown domain')
    cfg = settings[domain]
    rng = random.Random(seed + (0 if domain == 'gold' else 10000))
    examples, revisions = [], []
    for i in range(cfg['n']):
        t = 100 + i
        y = int(rng.random() < cfg['base'])
        early = y if rng.random() < cfg['early_accuracy'] else 1-y
        final = y if rng.random() < cfg['final_accuracy'] else 1-y
        key = f'{domain}-{i:04d}'
        examples.append(Example(key, t, y, t + cfg['label_delay']))
        revisions.extend((Revision(key, t-1, t-1, 1, early),
                          Revision(key, t-1, t+cfg['feature_delay'], 2, final)))
    return examples, revisions


def benchmark(domain, seed=434):
    examples, revisions = synthetic_domain(domain, seed)
    strict = feature_snapshot(examples, revisions, True)
    leaky = feature_snapshot(examples, revisions, False)
    folds = list(walk_forward_folds(examples))
    correct = {'strict': 0, 'leaky': 0}
    total = 0
    for train, test in folds:
        total += len(test)
        for name, snapshots in [('strict', strict), ('leaky', leaky)]:
            hits, _ = score(train, test, snapshots)
            correct[name] += hits
    assert all(r.available_at <= e.decision_at for e in examples
               for r in [strict[e.key]])
    return dict(domain=domain, folds=len(folds), evaluated=total,
                strict_correct=correct['strict'], leaky_correct=correct['leaky'],
                strict_accuracy=round(correct['strict']/total, 4),
                leaky_accuracy=round(correct['leaky']/total, 4),
                future_revision_fraction=round(sum(leaky[e.key].available_at > e.decision_at
                                                   for e in examples)/len(examples), 4),
                first_fold_train=len(folds[0][0]))


if __name__ == '__main__':
    import json
    print(json.dumps([benchmark(d) for d in ('gold', 'seo')], indent=2))

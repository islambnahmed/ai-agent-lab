"""Offline-policy-selection audit: synthetic only, Python 3.10+ standard library."""
import json
import math
import random
from statistics import NormalDist

BASELINE = 0.5
Z95 = NormalDist().inv_cdf(0.95)


def generate(n, domain, rng):
    if domain not in ('seo', 'gold'):
        raise ValueError('domain must be seo or gold')
    rows = []
    for _ in range(n):
        context, action = rng.randrange(8), rng.randrange(2)
        reward = float(rng.random() < 0.5) if domain == 'seo' else rng.gauss(0.5, 1.5)
        rows.append((context, action, reward))
    return rows


def evaluate(rows, policy):
    """SNIPS ratio estimate and iid influence-function standard error.

    Uniform binary logging: weight is 2 when action matches policy.
    Returns None if target action was never logged (no support in sample).
    """
    if not rows:
        return None
    observed = [reward for context, action, reward in rows if action == ((policy >> context) & 1)]
    if not observed:
        return None
    mean = sum(observed) / len(observed)
    # Ratio-estimator influence function: sqrt(sum(w^2*(r-mu)^2))/sum(w).
    se = math.sqrt(sum((reward - mean) ** 2 for reward in observed)) / len(observed)
    return mean, se


def run(domain, reps=300, train_n=350, audit_n=350, k=128, seed=444):
    if reps < 1 or train_n < 1 or audit_n < 1 or not 1 <= k <= 256:
        raise ValueError('invalid benchmark configuration')
    rng = random.Random(seed + (0 if domain == 'seo' else 100000))
    z_bonf = NormalDist().inv_cdf(1 - 0.05 / k)
    counts = dict(naive_false=0, bonf_false=0, independent_audit_false=0,
                  reused_audit_false=0, train_positive_bias=0, audit_positive_bias=0)
    sums = dict(train_selected=0., audit_selected=0., audit_reused_max=0.)
    for _ in range(reps):
        train = generate(train_n, domain, rng)
        audit = generate(audit_n, domain, rng)
        policies = rng.sample(range(256), k)  # all true values exactly 0.5
        train_est = [evaluate(train, p) for p in policies]
        winner_index = max(range(k), key=lambda j: train_est[j][0])
        train_mu, train_se = train_est[winner_index]
        audit_mu, audit_se = evaluate(audit, policies[winner_index])
        # Deliberate invalid counterexample: choose policy using the audit set.
        audit_est = [evaluate(audit, p) for p in policies]
        reused_mu, reused_se = max(audit_est, key=lambda pair: pair[0])
        counts['naive_false'] += train_mu - Z95 * train_se > BASELINE
        counts['bonf_false'] += any(mu - z_bonf * se > BASELINE for mu, se in train_est)
        counts['independent_audit_false'] += audit_mu - Z95 * audit_se > BASELINE
        counts['reused_audit_false'] += reused_mu - Z95 * reused_se > BASELINE
        counts['train_positive_bias'] += train_mu > BASELINE
        counts['audit_positive_bias'] += audit_mu > BASELINE
        sums['train_selected'] += train_mu
        sums['audit_selected'] += audit_mu
        sums['audit_reused_max'] += reused_mu
    return {
        'domain': domain, 'repetitions': reps, 'train_n': train_n, 'audit_n': audit_n,
        'candidate_policies': k, 'seed': seed, 'true_policy_value': BASELINE,
        'mean_estimates': {key: round(value / reps, 6) for key, value in sums.items()},
        'false_positive_rates': {key: round(value / reps, 6) for key, value in counts.items()},
        'method': 'SNIPS, iid influence-function SE, one-sided alpha=.05; Bonferroni alpha/K'
    }


def main():
    print(json.dumps({'experiments': [run('seo'), run('gold')]}, indent=2))


if __name__ == '__main__':
    main()

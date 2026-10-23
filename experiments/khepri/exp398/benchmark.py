"""Reproducible benchmark for selection optimism and honest holdout estimates."""
from selection_audit import Row, select_threshold, evaluate_fixed_policy
from statistics import mean, stdev
from math import sqrt
from random import Random
import argparse, json

SEED = 3982026
REPEATS = 100
N_TRAIN = 900
N_HOLDOUT = 900
N_DEPLOY = 900
THRESHOLDS = tuple(round(.35 + .05*i, 2) for i in range(13))  # .35 through .95


def correctness_probability(domain, confidence, shift=0.0):
    if domain == 'gold':
        return max(.01, min(.99, confidence - .18 - shift))
    if domain == 'seo':
        return max(.01, min(.99, .08 + .70*confidence - shift))
    raise ValueError('unknown domain')


def sample(rng, domain, n, audit_q, shift=0.0):
    observed = []
    latent = []
    for _ in range(n):
        confidence = rng.uniform(.30, .98) if domain == 'gold' else rng.uniform(.10, .93)
        correct = rng.random() < correctness_probability(domain, confidence, shift)
        logged_accept = confidence >= .75
        # q for abstentions; all accepted cases have observed labels.
        propensity = 1.0 if logged_accept else audit_q
        included = logged_accept or rng.random() < audit_q
        observed.append(Row(confidence, correct if included else None, propensity))
        latent.append((confidence, correct))
    return observed, latent


def true_value(latent, threshold):
    return mean((1.0 if correct else -2.0) if conf >= threshold else -.15
                for conf, correct in latent)


def run_trial(rng, domain, q, shift):
    train, train_latent = sample(rng, domain, N_TRAIN, q)
    holdout, holdout_latent = sample(rng, domain, N_HOLDOUT, q)
    _, deploy_latent = sample(rng, domain, N_DEPLOY, q, shift=shift)
    naive = select_threshold(train, THRESHOLDS, penalty=0)
    cautious = select_threshold(train, THRESHOLDS, penalty=1.96)
    oracle = max(THRESHOLDS, key=lambda t: true_value(train_latent, t))
    t = naive['threshold']
    h = evaluate_fixed_policy(holdout, t)
    return {
        'chosen_threshold': t,
        'train_optimism': naive['train_estimate'] - true_value(train_latent, t),
        'holdout_error': h['estimate'] - true_value(holdout_latent, t),
        'holdout_ci_covers_holdout_truth': float(h['ci95'][0] <= true_value(holdout_latent, t) <= h['ci95'][1]),
        'selected_train_truth': true_value(train_latent, t),
        'selected_deploy_truth': true_value(deploy_latent, t),
        'holdout_vs_deploy_gap': h['estimate'] - true_value(deploy_latent, t),
        'cautious_deploy_truth': true_value(deploy_latent, cautious['threshold']),
        'oracle_train_truth': true_value(train_latent, oracle),
        'fixed_deploy_truth': true_value(deploy_latent, .75),
        'cautious_threshold': cautious['threshold'],
        'holdout_estimate': h['estimate'],
    }


def ci_of_mean(values):
    center = mean(values)
    half = 1.96 * stdev(values) / sqrt(len(values))
    return [round(center-half, 5), round(center+half, 5)]


def run(repeats=REPEATS):
    rng = Random(SEED)
    out = {'experiment':'exp398', 'seed':SEED, 'replicates':repeats,
           'train_n':N_TRAIN, 'holdout_n':N_HOLDOUT, 'deploy_n':N_DEPLOY,
           'threshold_grid':list(THRESHOLDS), 'reward':{'correct':1,'wrong':-2,'abstain':-.15},
           'results':{}}
    for domain in ('gold','seo'):
        for q in (.02, .10):
            for shift in (0.0, .20):
                key=f'{domain}_q{q:.2f}_shift{shift:.2f}'
                trials=[run_trial(rng,domain,q,shift) for _ in range(repeats)]
                fields=('train_optimism','holdout_error','holdout_ci_covers_holdout_truth',
                        'selected_train_truth','selected_deploy_truth','holdout_vs_deploy_gap',
                        'cautious_deploy_truth','oracle_train_truth','fixed_deploy_truth',
                        'chosen_threshold','cautious_threshold','holdout_estimate')
                row={k:round(mean(t[k] for t in trials),5) for k in fields}
                row['train_optimism_ci95']=ci_of_mean([t['train_optimism'] for t in trials])
                row['holdout_error_ci95']=ci_of_mean([t['holdout_error'] for t in trials])
                row['holdout_vs_deploy_gap_ci95']=ci_of_mean([t['holdout_vs_deploy_gap'] for t in trials])
                out['results'][key]=row
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--write',action='store_true');p.add_argument('--repeats',type=int,default=REPEATS)
    args=p.parse_args()
    report=run(args.repeats)
    print(json.dumps(report,indent=2))
    if args.write:
        from pathlib import Path
        Path(__file__).with_name('results.json').write_text(json.dumps(report,indent=2)+'\n')

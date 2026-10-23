"""Reproducible synthetic selective-feedback benchmark, no external data."""
from selective_audit import Record, selective_accuracy, audit_accuracy, policy_value
from statistics import mean, stdev
import math
import random, json, argparse

SEED=3972026
N=3000
REPEATS=200
LOG_THRESHOLD=.75
ALT_THRESHOLD=.65
AUDIT_PROB=.10

def reward(correct): return 1.0 if correct else -2.0

def true_value(items, threshold):
    return mean(reward(correct) if confidence>=threshold else -.15 for confidence,correct in items)

def trial(rng, domain, adversarial=False):
    items=[]; records=[]
    for _ in range(N):
        if domain=='gold':
            confidence=rng.uniform(.30,.98)
            probability=max(.02,min(.98,confidence-.18))
        else:
            confidence=rng.uniform(.10,.93)
            probability=max(.02,min(.98,.08+.70*confidence))
        correct=rng.random()<probability
        accepted=confidence>=LOG_THRESHOLD
        # Independent audit: q=.10. Adversarial counterexample: selection
        # depends on the unobserved outcome but logger incorrectly records .10.
        actual_q=(.20 if correct else .025) if adversarial else AUDIT_PROB
        observed=accepted or rng.random()<actual_q
        inclusion=1 if accepted else AUDIT_PROB
        items.append((confidence,correct))
        records.append(Record(confidence,accepted,correct if observed else None,inclusion))
    observed_rows=[r for r in records if r.observed_correct is not None]
    naive_alt=mean(reward(r.observed_correct) if r.confidence>=ALT_THRESHOLD else -.15 for r in observed_rows)
    return {
        'coverage':sum(r.accepted for r in records)/N,
        'true_population_accuracy':mean(c for _,c in items),
        'selective_accuracy':selective_accuracy(records),
        'audit_estimated_population_accuracy':audit_accuracy(records),
        'true_alternative_policy_value':true_value(items,ALT_THRESHOLD),
        'audited_alternative_policy_value':policy_value(records,ALT_THRESHOLD),
        'naive_labeled_only_alternative_policy_value':naive_alt,
        'true_logged_policy_value':true_value(items,LOG_THRESHOLD),
    }

def run():
    rng=random.Random(SEED)
    report={'experiment':'exp397','seed':SEED,'n_per_replicate':N,'replicates_per_domain_and_scenario':REPEATS,
        'logging_threshold':LOG_THRESHOLD,'alternative_threshold':ALT_THRESHOLD,
        'nominal_audit_probability':AUDIT_PROB,
        'reward':{'correct':1,'incorrect':-2,'abstain':-.15},'domains':{}}
    for domain in ['gold','seo']:
        report['domains'][domain]={}
        for scenario in ['independent_audit','outcome_dependent_audit']:
            runs=[trial(rng,domain,adversarial=(scenario=='outcome_dependent_audit')) for _ in range(REPEATS)]
            summary={k:round(mean(x[k] for x in runs),6) for k in runs[0]}
            summary['accuracy_estimation_bias']=round(summary['audit_estimated_population_accuracy']-summary['true_population_accuracy'],6)
            summary['policy_value_estimation_bias']=round(summary['audited_alternative_policy_value']-summary['true_alternative_policy_value'],6)
            summary['naive_policy_value_bias']=round(summary['naive_labeled_only_alternative_policy_value']-summary['true_alternative_policy_value'],6)
            for field,estimate,truth in [
                ('accuracy','audit_estimated_population_accuracy','true_population_accuracy'),
                ('policy_value','audited_alternative_policy_value','true_alternative_policy_value')]:
                differences=[x[estimate]-x[truth] for x in runs]
                center=mean(differences)
                halfwidth=1.96*stdev(differences)/math.sqrt(len(differences))
                summary[field+'_bias_95pct_ci']=[round(center-halfwidth,6),round(center+halfwidth,6)]
            report['domains'][domain][scenario]=summary
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');args=p.parse_args()
    r=run();print(json.dumps(r,indent=2))
    if args.write:
        from pathlib import Path
        Path(__file__).with_name('results.json').write_text(json.dumps(r,indent=2)+'\n')

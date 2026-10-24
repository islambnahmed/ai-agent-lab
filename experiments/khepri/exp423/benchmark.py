"""Seeded synthetic Monte Carlo: deliberately adversarial within-cluster dependence."""
import json
import random
from cluster_evidence import ClusterAudit

SEED = 423
REPLICATES = 2000
CLUSTERS = 80


def trial(rng, p, cluster_size=8, noise=0., global_shock=False, variable_size=False, persistence=None, randomize_cluster=False):
    audit = ClusterAudit()
    global_sign = 1 if rng.random() < p else -1
    persistent_sign = global_sign
    for index in range(CLUSTERS):
        if persistence is not None and index > 0 and rng.random() >= persistence:
            persistent_sign = -persistent_sign
        sign = (persistent_sign if persistence is not None else
                (global_sign if global_shock else (1 if rng.random() < p else -1)))
        if randomize_cluster:
            sign *= (1 if rng.random() < .5 else -1)
        size = rng.randint(1, 12) if variable_size else cluster_size
        gains = [sign if rng.random() >= noise else -sign for _ in range(size)]
        audit.add_cluster(gains)
    return (audit.event_naive.first_crossing is not None,
            audit.clustered.first_crossing is not None)


def run(replicates=REPLICATES):
    scenarios = {
        'seo_null_8_identical': dict(p=.5, noise=0.),
        'seo_positive_8_identical': dict(p=.62, noise=0.),
        'seo_null_singletons': dict(p=.5, cluster_size=1),
        'finance_null_noisy_variable': dict(p=.5, noise=.12, variable_size=True),
        'finance_positive_noisy_variable': dict(p=.65, noise=.12, variable_size=True),
        'shared_global_shock_counterexample': dict(p=.5, noise=0., global_shock=True),
        'persistent_regime_counterexample': dict(p=.5, noise=.12, persistence=.95),
        'persistent_regime_randomized_clusters': dict(p=.5, noise=.12, persistence=.95, randomize_cluster=True),
    }
    out = {'seed': SEED, 'replicates_per_scenario': replicates, 'clusters_per_trial': CLUSTERS,
           'alpha': .05, 'synthetic': True, 'scenarios': {}}
    for i, (name, args) in enumerate(scenarios.items()):
        rng = random.Random(SEED + 1000 * i)
        event_rejects = cluster_rejects = 0
        for _ in range(replicates):
            event, cluster = trial(rng, **args)
            event_rejects += event
            cluster_rejects += cluster
        out['scenarios'][name] = {
            'event_level_rejections': event_rejects,
            'cluster_level_rejections': cluster_rejects,
            'event_level_rate': round(event_rejects / replicates, 5),
            'cluster_level_rate': round(cluster_rejects / replicates, 5),
            'params': args,
        }
    return out


if __name__ == '__main__':
    print(json.dumps(run(), indent=2, sort_keys=True))

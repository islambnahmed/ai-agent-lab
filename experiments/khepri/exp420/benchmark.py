"""Deterministic seeded interference benchmark, not real attack incidence."""
import json
import random
from state_bound import FakeStore, Approver, plan


def run(seed=420, n=5000):
    rng = random.Random(seed)
    result = {'seed': seed, 'per_domain': n, 'domains': {}}
    for domain in ('seo', 'gold'):
        stats = {mode: {'accepted': 0, 'stale_overwrites': 0, 'false_conflicts': 0,
                        'legitimate_successes': 0, 'aba_blocked': 0}
                 for mode in ('baseline', 'version_bound')}
        for i in range(n):
            # Repeat identical scenario on both policies, for fair paired comparison.
            scenario = rng.choice(('clean', 'intervening', 'aba', 'unrelated', 'create_race'))
            for mode in stats:
                s = FakeStore()
                p = plan(f'{domain}_{i}.txt')
                if scenario != 'create_race':
                    s.seed(p.path, b'original')
                a = Approver(s, bind_version=(mode == 'version_bound'))
                token = a.issue(p, b'agent')
                if scenario in ('intervening', 'aba'):
                    s.seed(p.path, b'peer')
                if scenario == 'aba':
                    s.seed(p.path, b'original')
                if scenario == 'unrelated':
                    s.seed(plan(f'{domain}_{i}_other.txt').path, b'peer')
                if scenario == 'create_race':
                    s.seed(p.path, b'peer-created')
                outcome = a.redeem(token, p, b'agent')
                if outcome.accepted:
                    stats[mode]['accepted'] += 1
                if outcome.accepted and scenario in ('intervening', 'aba', 'create_race'):
                    stats[mode]['stale_overwrites'] += 1
                if not outcome.accepted and scenario in ('clean', 'unrelated'):
                    stats[mode]['false_conflicts'] += 1
                if outcome.accepted and scenario in ('clean', 'unrelated'):
                    stats[mode]['legitimate_successes'] += 1
                if not outcome.accepted and scenario == 'aba':
                    stats[mode]['aba_blocked'] += 1
        result['domains'][domain] = stats
    return result


if __name__ == '__main__':
    print(json.dumps(run(), indent=2, sort_keys=True))

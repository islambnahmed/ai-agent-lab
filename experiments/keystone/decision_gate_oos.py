"""Out-of-sample Keystone gate falsification; run: python decision_gate_oos.py (numpy)."""
import numpy as np

P0, T = .9, 100
QS = (.9, .7, .5, .3, .1)
HS = tuple(range(3, 10))
TRAIN = [(c, s) for c in (2, 4, 8, 16) for s in (.2, .5, 1.)]
TEST = [(3, .35), (5, .65), (10, .8), (12, .3), (6, 1.2), (9, 1.), (20, 1.5)]


def paths(q, n, seed):
    x = np.random.default_rng(seed).random((n, T)) < q
    fast = slow = np.full(n, P0)
    ones = np.zeros(n, dtype=int)
    f, s, g = [np.empty((n, T), dtype=np.float32) for _ in range(3)]
    running_glr = np.zeros(n)
    for t in range(T):
        f[:, t], s[:, t], g[:, t] = fast, slow, running_glr
        obs = x[:, t]
        fast = .7 * fast + .3 * obs
        slow = .97 * slow + .03 * obs
        ones += obs
        mle = np.minimum(ones / (t + 1), P0)
        kl = np.zeros(n)
        mask = mle > 0
        kl[mask] += mle[mask] * np.log(mle[mask] / P0)
        mask = mle < 1
        kl[mask] += (1 - mle[mask]) * np.log((1 - mle[mask]) / (1 - P0))
        running_glr = np.maximum(running_glr, (t + 1) * kl)
    return f, s, g


def sample(n, seed):
    return {q: paths(q, n, seed + 100 * i) for i, q in enumerate(QS)}


def regret(data, q, c, safe, h):
    fast, slow, gate = data
    estimate = slow if h == 'adapt' else np.where(gate >= h, fast, slow)
    risky_loss = c * (1 - q)
    oracle_loss = min(risky_loss, safe)
    return np.sum(np.where(c * (1 - estimate) < safe, risky_loss, safe) - oracle_loss, axis=1)


def mean_scores(data, cost):
    c, safe = cost
    return {h: np.mean(np.concatenate([regret(data[q], q, c, safe, h) for q in QS]))
            for h in (*HS, 'adapt')}


def bucket(cost):
    r = cost[1] / cost[0]
    return 0 if r < .075 else (1 if r < .15 else 2)


def main():
    train, test = sample(4000, 20261008), sample(6000, 20261108)
    training = {cost: mean_scores(train, cost) for cost in TRAIN}

    def choose(costs, options):
        return min(options, key=lambda h: np.mean([training[c][h] / c[0] for c in costs]))

    fixed = choose(TRAIN, HS)
    bucket_only = {b: choose([c for c in TRAIN if bucket(c) == b], HS)
                   for b in range(3)}
    abstain = {b: choose([c for c in TRAIN if bucket(c) == b], (*HS, 'adapt'))
               for b in range(3)}
    safe = {b: choose([c for c in TRAIN if bucket(c) == b], (5, 6, 7, 8, 9, 'adapt'))
            for b in range(3)}
    print('fixed:', fixed, 'bucket:', bucket_only, 'abstain:', abstain, 'budget:', safe)
    scores = {c: mean_scores(test, c) for c in TEST}
    policies = {'adapt': lambda c: 'adapt', 'fixed': lambda c: fixed,
                'bucket': lambda c: bucket_only[bucket(c)],
                'abstain': lambda c: abstain[bucket(c)],
                'budget': lambda c: safe[bucket(c)]}
    for label, select in policies.items():
        value = np.mean([scores[c][select(c)] / c[0] for c in TEST])
        print(label, 'held-out mean normalized regret:', round(value, 5))
    print('Held-out costs (C, safe, adapt, abstain, budget):')
    for c in TEST:
        d = scores[c]
        print(c, round(d['adapt'], 3), round(d[abstain[bucket(c)]], 3),
              round(d[safe[bucket(c)]], 3))

    # Reused trajectories across cost contexts: cluster paired differences by (q, path).
    for label, select in [('abstain', policies['abstain']), ('budget', policies['budget'])]:
        clusters = []
        for q in QS:
            paired = [(regret(test[q], q, *c, select(c)) -
                       regret(test[q], q, *c, 'adapt')) / c[0] for c in TEST]
            clusters.append(np.mean(paired, axis=0))
        d = np.concatenate(clusters)
        ci = 1.96 * d.std(ddof=1) / np.sqrt(len(d))
        print(label, 'minus adapt: mean', round(d.mean(), 5),
              'conditional Monte Carlo 95% CI', tuple(round(v, 5)
              for v in (d.mean() - ci, d.mean() + ci)))
    g = test[.9][2]
    print('No-change gate crossing by final pre-action time:',
          {h: round(float((g[:, -1] >= h).mean()), 5) for h in HS})


if __name__ == '__main__':
    main()

"""Worker A: noise-aware finite-grammar falsification, with paired acquisition policies.

Synthetic six-bit parity hypotheses vs nonlinear bitcount-threshold targets.
Queries never see the hidden target. A one-sided exact binomial-tail test rejects
only when *every* candidate has too many observed errors. Under an in-grammar
truth and independent binary label flips with probability <= p0, a rejection at
any of the predeclared checkpoints has probability <= alpha (Bonferroni).
The bound is valid even for adaptively selected, nonrepeated inputs because
unqueried label noise is independent of the past. Not robust to correlated,
adversarial, instance-dependent, or underestimated noise.

Dependencies: numpy. Example:
  python worker_a_noise_robust_audit.py --episodes 400 --seed 20261008
"""
import argparse
import json
from math import comb
from random import Random
import numpy as np

N_INPUTS = 64
BUDGET = 32
CHECKPOINTS = (8, 12, 16, 20, 24, 32)
STRATEGIES = ('random', 'active', 'audit', 'alternate', 'audit_then_random')
MASKS = [(mask, bias) for mask in range(1, 64) for bias in (0, 1)]
PRED = np.array([[(int(x & mask).bit_count() & 1) ^ bias for x in range(64)]
                 for mask, bias in MASKS], dtype=np.int8)


def tail(n, k, p):
    """P[Binomial(n,p) >= k], including p=0 and p=1."""
    if not (0 <= p <= 1) or not (0 <= k <= n + 1):
        raise ValueError((n, k, p))
    if k == 0:
        return 1.0
    if k == n + 1:
        return 0.0
    return sum(comb(n, j) * p**j * (1-p)**(n-j) for j in range(k, n+1))


def choose(strategy, step, remaining, losses, rng):
    """Acquisition depends only on prior observed errors, not target or noise map."""
    if strategy == 'audit_then_random':
        strategy = 'audit' if step <= 6 else 'random'
    elif strategy == 'alternate':
        strategy = 'active' if step % 2 else 'audit'
    if strategy == 'random':
        return rng.choice(remaining)
    elite = losses <= losses.min() + 1
    votes = PRED[elite][:, remaining].sum(axis=0)
    n = int(elite.sum())
    disagreement = votes * (n - votes)
    extreme = disagreement.max() if strategy == 'active' else disagreement.min()
    tied = [x for x, score in zip(remaining, disagreement) if score == extreme]
    return rng.choice(tied)


def observe(labels, strategy, seed, p0, alpha=0.01):
    rng = Random(seed)
    remaining = list(range(N_INPUTS))
    losses = np.zeros(len(MASKS), dtype=np.int16)
    rejections = {}
    trajectory = []
    for step in range(1, BUDGET+1):
        x = choose(strategy, step, remaining, losses, rng)
        remaining.remove(x)
        y = int(labels[x])
        losses += (PRED[:, x] != y)
        trajectory.append((x, y))
        if step in CHECKPOINTS:
            best_loss = int(losses.min())
            pvalue = tail(step, best_loss, p0)
            rejections[step] = bool(pvalue <= alpha / len(CHECKPOINTS))
    # First rejection is persistent as an observed event, even if later p-value grows.
    return rejections, trajectory


def experiment(episodes=200, seed=20261008, alpha=0.01):
    if episodes < 1 or not 0 < alpha < 1:
        raise ValueError('episodes>=1 and 0<alpha<1 required')
    result = {}
    for noise, p0 in ((0.0, 0.0), (0.05, 0.10), (0.10, 0.10)):
        key = str(noise)
        result[key] = {}
        for kind in ('in_grammar', 'out_of_grammar'):
            count = {strategy: {str(k): 0 for k in CHECKPOINTS} for strategy in STRATEGIES}
            paired = {strategy: {str(k): {'wins': 0, 'losses': 0, 'ties': 0}
                                  for k in CHECKPOINTS}
                      for strategy in STRATEGIES if strategy != 'random'}
            for episode in range(episodes):
                erng = Random(seed + episode * 1000003 + (0 if kind == 'in_grammar' else 1700017))
                if kind == 'in_grammar':
                    true = PRED[erng.randrange(len(MASKS))].copy()
                else:
                    threshold = erng.choice((2, 3, 4, 5))
                    true = np.array([int(x.bit_count() >= threshold) for x in range(64)], dtype=np.int8)
                # A shared potential-outcome noise map makes comparisons paired.
                # Different x values receive independent flips.
                flips = np.array([int(erng.random() < noise) for _ in range(64)], dtype=np.int8)
                labels = true ^ flips
                detections = {}
                for si, strategy in enumerate(STRATEGIES):
                    rejects, _ = observe(labels, strategy,
                                         seed + episode*65537 + si*4919 +
                                         (0 if kind == 'in_grammar' else 71237), p0, alpha)
                    detected = False
                    detections[strategy] = {}
                    for k in CHECKPOINTS:
                        detected |= rejects[k]
                        detections[strategy][k] = detected
                        count[strategy][str(k)] += detected
                for strategy in STRATEGIES[1:]:
                    for k in CHECKPOINTS:
                        a, b = detections[strategy][k], detections['random'][k]
                        field = 'wins' if a and not b else 'losses' if b and not a else 'ties'
                        paired[strategy][str(k)][field] += 1
            result[key][kind] = {'episodes': episodes, 'p0': p0, 'alpha_familywise': alpha,
                                 'detections': count, 'paired_vs_random': paired}
    return result


def correlated_noise_stress(episodes=800, seed=20261008, alpha=0.01):
    """Deliberately violate independence while keeping per-input marginal P(flip)<=.10.

    With probability .10 an episode receives a shared nonlinear corruption
    shock: every input with popcount>=3 is flipped. Otherwise no input flips.
    This is NOT a valid test of the independent-noise theorem; it measures
    how badly a false guarantee can fail under correlated observations.
    """
    shock_mask = np.array([int(x.bit_count() >= 3) for x in range(64)], dtype=np.int8)
    counts = {strategy: 0 for strategy in STRATEGIES}
    shocks = 0
    for episode in range(episodes):
        rng = Random(seed + episode*1000003 + 870017)
        truth = PRED[rng.randrange(len(MASKS))]
        shock = rng.random() < 0.10
        shocks += shock
        labels = truth ^ (shock_mask if shock else 0)
        for si, strategy in enumerate(STRATEGIES):
            rejects, _ = observe(labels, strategy, seed + episode*65537 + si*4919, .10, alpha)
            counts[strategy] += any(rejects.values())
    return {'episodes': episodes, 'shocks': shocks, 'per_input_flip_probability_upper_bound': .10,
            'independent_noise_assumption_satisfied': False,
            'false_rejections': counts}


def self_test():
    assert len(MASKS) == 126 and PRED.shape == (126, 64)
    assert tail(4, 1, 0) == 0 and tail(4, 0, 0) == 1
    assert abs(tail(4, 2, .5) - 11/16) < 1e-12
    assert all(tail(20, k+1, .1) <= tail(20, k, .1) for k in range(20))
    labels = PRED[7]
    for strategy in STRATEGIES:
        rejects, history = observe(labels, strategy, 3, p0=0)
        assert not any(rejects.values()) and len({x for x, _ in history}) == BUDGET
    a = experiment(episodes=2, seed=11)
    b = experiment(episodes=2, seed=11)
    assert a == b
    assert correlated_noise_stress(2, 11) == correlated_noise_stress(2, 11)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--episodes', type=int, default=200)
    parser.add_argument('--seed', type=int, default=20261008)
    parser.add_argument('--output', default=None)
    args = parser.parse_args()
    self_test()
    result = {'independent_noise': experiment(episodes=args.episodes, seed=args.seed),
              'correlated_noise_stress': correlated_noise_stress(args.episodes, args.seed)}
    data = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(data + '\n')
    else:
        print(data)

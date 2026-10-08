"""Independent Worker A: finite-grammar novelty acquisition benchmark.

Noiseless, finite synthetic tasks. Compares random sampling, disagreement
(active identification), agreement (audit/falsification), and alternation.
No oracle/target access by acquisition. Python standard library only.

Example: python experiments/worker_a_grammar_audit.py --episodes 500 --seed 1001
"""
import argparse
import json
from collections import Counter
from random import Random


def domain(family):
    return range(31 if family == "affine" else 64)


def grammar(family):
    if family == "affine":
        return [(a, b) for a in range(1, 31) for b in range(31)]
    if family == "parity":
        return [(mask, bias) for mask in range(1, 64) for bias in (0, 1)]
    raise ValueError(family)


def predict(family, h, x):
    a, b = h
    if family == "affine":
        return ((a * x + b) % 31) // 5
    return ((x & a).bit_count() & 1) ^ b


def out_of_grammar_target(family, rng):
    if family == "affine":
        a, b = rng.randrange(31), rng.randrange(31)
        return lambda x: ((x*x + a*x + b) % 31) // 5
    threshold = rng.choice((2, 3, 4, 5))
    return lambda x: int(x.bit_count() >= threshold)


def disagreement(family, viable, x):
    counts = Counter(predict(family, h, x) for h in viable)
    return len(viable)**2 - sum(c*c for c in counts.values())


def acquire(family, viable, unused, rng, strategy, step):
    if strategy == "random":
        return rng.choice(unused)
    if strategy == "alternate":
        strategy = "active" if step % 2 else "audit"
    scores = [(disagreement(family, viable, x), x) for x in unused]
    extreme = (max if strategy == "active" else min)(s for s, _ in scores)
    return rng.choice([x for score, x in scores if score == extreme])


def contradiction_certificate(family, observations, candidates):
    return not any(all(predict(family, h, x) == y for x, y in observations)
                   for h in candidates)


def observe(family, target, candidates, budget, rng, strategy):
    unused = list(domain(family))
    viable = list(candidates)
    history = []
    for step in range(1, budget+1):
        x = acquire(family, viable, unused, rng, strategy, step)
        unused.remove(x)
        y = target(x)
        history.append((x, y))
        viable = [h for h in viable if predict(family, h, x) == y]
        if not viable:
            assert contradiction_certificate(family, history, candidates)
            return step, history
    return None, history


def run(episodes=500, seed=1001, budget=12):
    if episodes < 1 or not 1 <= budget <= 31:
        raise ValueError("episodes>=1 and 1<=budget<=31 required")
    strategies = ("random", "active", "audit", "alternate")
    result = {}
    for family in ("affine", "parity"):
        hs = grammar(family)
        stats = {"episodes": episodes, "candidate_count": len(hs),
                 "detections": {}, "paired_vs_random": {}, "witness": None}
        for kind in ("in_grammar", "out_of_grammar"):
            stats["detections"][kind] = {s: [0]*budget for s in strategies}
            if kind == "out_of_grammar":
                stats["paired_vs_random"] = {
                    s: {str(k): {"wins": 0, "losses": 0, "ties": 0}
                        for k in (4, 6, 8, 12)}
                    for s in strategies if s != "random"
                }
            for episode in range(episodes):
                episode_seed = (seed + episode*2654435761
                                + (0 if kind == "in_grammar" else 90000013)
                                + (0 if family == "affine" else 14000011))
                target_rng = Random(episode_seed)
                if kind == "in_grammar":
                    h = target_rng.choice(hs)
                    target = lambda x, h=h: predict(family, h, x)
                else:
                    target = out_of_grammar_target(family, target_rng)
                first_by_strategy = {}
                for index, strategy in enumerate(strategies):
                    first, history = observe(
                        family, target, hs, budget,
                        Random(episode_seed + index*479001599), strategy
                    )
                    first_by_strategy[strategy] = first
                    if kind == "in_grammar" and first is not None:
                        raise AssertionError("false alarm on realizable target")
                    if first is not None:
                        if kind == "out_of_grammar" and stats["witness"] is None:
                            stats["witness"] = {"first": first, "history": history}
                        for j in range(first-1, budget):
                            stats["detections"][kind][strategy][j] += 1
                if kind == "out_of_grammar":
                    for strategy in strategies[1:]:
                        for k in (4, 6, 8, 12):
                            a = first_by_strategy[strategy]
                            b = first_by_strategy["random"]
                            aa = a is not None and a <= k
                            bb = b is not None and b <= k
                            label = ("wins" if aa and not bb else
                                     "losses" if bb and not aa else "ties")
                            stats["paired_vs_random"][strategy][str(k)][label] += 1
        result[family] = stats
    return result


def self_test():
    for family in ("affine", "parity"):
        hs = grammar(family)
        for h in hs[::max(1, len(hs)//8)]:
            for strategy in ("random", "active", "audit", "alternate"):
                first, observations = observe(
                    family, lambda x, h=h: predict(family, h, x),
                    hs, 12, Random(42), strategy
                )
                assert first is None
                assert len({x for x, _ in observations}) == 12
        assert contradiction_certificate(family, [(0, 10 if family == "affine" else 2)], hs)
    # Explicit four-point impossibility for affine parity Boolean labels:
    hs = grammar("parity")
    witness = [(0, 0), (1, 0), (2, 0), (3, 1)]
    assert contradiction_certificate("parity", witness, hs)
    assert run(episodes=2, seed=11) == run(episodes=2, seed=11)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--episodes", type=int, default=500)
    p.add_argument("--seed", type=int, default=1001)
    p.add_argument("--budget", type=int, default=12)
    args = p.parse_args()
    self_test()
    print(json.dumps(run(args.episodes, args.seed, args.budget), indent=2))

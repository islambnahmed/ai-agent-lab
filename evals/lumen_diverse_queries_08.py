"""Lumen 08: equal-cost query diversity versus repetition under correlated noise.

Toy finite permutation DSL, not a general intelligence demonstration.
Noise mechanisms: independent per call, persistent per input, global per episode.
A five-call budget is identical for both policies. Identifiability is evaluated
on candidate lengths 2..8; generalization is checked separately on 9..64.
"""
from itertools import product
from random import Random

OPS = ("reverse", "rotl1", "swap01")
PROGRAMS = [()] + [p for k in range(1, 5) for p in product(OPS, repeat=k)]
TRAIN_LENGTHS = tuple(range(2, 9))
HELDOUT_LENGTHS = tuple(range(9, 65))


def apply(program, xs):
    xs = tuple(xs)
    for op in program:
        if op == "reverse":
            xs = xs[::-1]
        elif op == "rotl1":
            xs = xs[1:] + xs[:1]
        elif op == "swap01":
            xs = xs[1:2] + xs[:1] + xs[2:]
        else:
            raise ValueError(op)
    return xs


def classes():
    seen = {}
    for p in PROGRAMS:
        signature = tuple(apply(p, tuple(range(n))) for n in TRAIN_LENGTHS)
        seen.setdefault(signature, p)
    return list(seen.items())


CLASSES = classes()
PROBES = {n: tuple(range(n)) for n in range(2, 13)}
PRED = {n: [apply(p, x) for _, p in CLASSES] for n, x in PROBES.items()}


def corrupt(y):
    return y[1:] + y[:1]


def observed(truth, n, rng, regime, sticky_cache, global_error):
    if regime == "iid":
        error = rng.random() < 0.2
    elif regime == "per_probe":
        if n not in sticky_cache:
            sticky_cache[n] = rng.random() < 0.2
        error = sticky_cache[n]
    elif regime == "global":
        error = global_error
    else:
        raise ValueError(regime)
    y = PRED[n][truth]
    return corrupt(y) if error else y


def identify(labels):
    # Minimize contradictions; never erase the target after one noisy label.
    losses = [sum(PRED[n][j] != y for n, y in labels) for j in range(len(CLASSES))]
    best = min(losses)
    winners = [j for j, loss in enumerate(losses) if loss == best]
    return winners, best


def trial(truth, regime, policy, seed):
    rng = Random(seed)
    global_error = rng.random() < 0.2 if regime == "global" else False
    sticky_cache = {}
    probes = (5, 5, 6, 6, 3) if policy == "repeat" else (3, 4, 5, 6, 7)
    labels = [(n, observed(truth, n, rng, regime, sticky_cache, global_error)) for n in probes]
    winners, loss = identify(labels)
    decided = len(winners) == 1
    correct = decided and winners[0] == truth
    return decided, correct, loss


def run(trials=80):
    assert len(PROGRAMS) == 121 and len(CLASSES) == 61
    # The finite DSL happens to have no hidden collisions beyond length 8.
    # Check this post hoc, not as part of the learner's observed labels.
    signatures = {}
    for p in PROGRAMS:
        train = tuple(apply(p, tuple(range(n))) for n in TRAIN_LENGTHS)
        held = tuple(apply(p, tuple(range(n))) for n in HELDOUT_LENGTHS)
        assert train not in signatures or signatures[train] == held
        signatures[train] = held
    # Both policies spend five calls and identify every semantic class with
    # noiseless labels; repeated probes trade diversity for repeated votes.
    assert len({tuple(PRED[n][j] for n in (3, 4, 5, 6, 7)) for j in range(61)}) == 61
    assert len({tuple(PRED[n][j] for n in (5, 6, 3)) for j in range(61)}) == 61
    results = {}
    by_target = {}
    for regime in ("iid", "per_probe", "global"):
        for policy in ("repeat", "diverse"):
            outcomes = [trial(t, regime, policy, 800000 + t * 1009 + i * 31)
                        for t in range(len(CLASSES)) for i in range(trials)]
            n = len(outcomes)
            by_target[(regime, policy)] = [sum(outcomes[t*trials+i][1] for i in range(trials))/trials
                                            for t in range(len(CLASSES))]
            decisions = sum(row[0] for row in outcomes)
            correct = sum(row[1] for row in outcomes)
            results[(regime, policy)] = {
                "runs": n, "oracle_calls_per_run": 5,
                "decided": decisions, "correct_decisions": correct,
                "wrong_decisions": decisions - correct,
                "abstained": n - decisions,
                "accuracy_all": round(correct / n, 4),
                "error_among_decided": round((decisions-correct) / decisions, 4) if decisions else None,
            }
    # Paired, class-cluster bootstrap: do not treat 80 seeds of one semantic
    # class as 80 independent classes when estimating policy uncertainty.
    gains = {}
    for regime in ("iid", "per_probe", "global"):
        deltas = [a - b for a, b in zip(by_target[(regime, "diverse")],
                                       by_target[(regime, "repeat")])]
        rng = Random(31)
        bootstrap = sorted(sum(deltas[rng.randrange(len(deltas))] for _ in deltas) / len(deltas)
                           for _ in range(3000))
        gains[regime] = {"gain_pp": round(100 * sum(deltas)/len(deltas), 2),
                         "class_bootstrap_95pct_pp": [round(100*bootstrap[75], 2),
                                                       round(100*bootstrap[2925], 2)]}
    # A fully correlated bias can perfectly impersonate another program.
    identity = next(j for j, (_, p) in enumerate(CLASSES) if p == ())
    rotl = next(j for j, (_, p) in enumerate(CLASSES) if p == ("rotl1",))
    global_labels = [(n, corrupt(PRED[n][identity])) for n in (3, 4, 5, 6, 7)]
    winners, loss = identify(global_labels)
    assert winners == [rotl] and loss == 0
    assert results[("per_probe", "diverse")]["correct_decisions"] > results[("per_probe", "repeat")]["correct_decisions"]
    assert gains["per_probe"]["class_bootstrap_95pct_pp"][0] > 0
    assert gains["global"]["gain_pp"] == 0
    for policy, probes in (("repeat", (5, 5, 6, 6, 3)),
                           ("diverse", (3, 4, 5, 6, 7))):
        for target in range(len(CLASSES)):
            winners, _ = identify([(n, PRED[n][target]) for n in probes])
            assert winners == [target], (policy, target)
    print("unique_semantic_programs:", len(CLASSES))
    for key, value in results.items():
        print(key, value)
    print("diverse_minus_repeat:", gains)
    print("global_bias_witness: identity labels become exactly rotl1; 5 diverse probes cannot detect it")
    return results


if __name__ == "__main__":
    run()

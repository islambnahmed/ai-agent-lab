#!/usr/bin/env python3
"""Synthetic bounded-memory transfer/shift benchmark; no third-party packages."""
import argparse
import itertools
import json
import random
import resource
import statistics
import time
import tracemalloc
from collections import Counter

INPUTS = list(itertools.product((0, 1), repeat=3))
PAIRS = list(itertools.combinations(range(3), 2))
FAMILIES = ("xor", "and", "or")
HYPOTHESES = list(itertools.product(FAMILIES, PAIRS, (0, 1)))

def output(x, h):
    family, pair, flip = h
    a, b = (x[i] for i in pair)
    bit = (a ^ b) if family == "xor" else ((a & b) if family == "and" else (a | b))
    return bit ^ flip

def task(rng, family):
    return (family, rng.choice(PAIRS), rng.randrange(2))

def examples(rng, h, k):
    xs = rng.sample(INPUTS, len(INPUTS))
    return [(x, output(x, h)) for x in xs[:k]], [(x, output(x, h)) for x in xs[k:]]

def posterior_predict(x, observed, family_weights):
    valid = [h for h in HYPOTHESES if all(output(xi, h) == yi for xi, yi in observed)]
    assert valid, "Generator must remain in hypothesis class"
    denom = sum(family_weights[h[0]] for h in valid)
    return sum(family_weights[h[0]] * output(x, h) for h in valid) / denom

def nearest_predict(x, observed):
    ds = [sum(a != b for a, b in zip(x, xi)) for xi, _ in observed]
    mind = min(ds)
    return statistics.mean(yi for (xi, yi), d in zip(observed, ds) if d == mind)

def score(tasks, k, seed, weights):
    rng = random.Random(seed)
    sums = {name: [0.0, 0.0, 0] for name in ("stateless", "retrieval", "uniform", "meta")}
    uniform = {f: 1.0 for f in FAMILIES}
    for h in tasks:
        seen, unseen = examples(rng, h, k)
        for x, y in unseen:
            ps = {
                "stateless": 0.5,
                "retrieval": nearest_predict(x, seen),
                "uniform": posterior_predict(x, seen, uniform),
                "meta": posterior_predict(x, seen, weights),
            }
            for name, p in ps.items():
                sums[name][0] += (p-y)**2
                sums[name][1] += (p >= 0.5) == bool(y)
                sums[name][2] += 1
    return {name: {"brier": round(v[0]/v[2], 6), "accuracy": round(v[1]/v[2], 6), "n": v[2]} for name, v in sums.items()}

def online_shift(tasks, k, seed, initial_weights, eta=0.1, block=20):
    """Update only after the current task's withheld outcomes are revealed."""
    rng = random.Random(seed)
    total = sum(initial_weights.values())
    ema = {f: initial_weights[f]/total for f in FAMILIES}
    blocks, losses = [], []
    for i, h in enumerate(tasks):
        seen, unseen = examples(rng, h, k)
        weights = {f: 0.02 + 0.94*ema[f] for f in FAMILIES}
        loss = statistics.mean((posterior_predict(x, seen, weights)-y)**2 for x,y in unseen)
        losses.append(loss)
        for f in FAMILIES:
            ema[f] = (1-eta)*ema[f] + eta*(f == h[0])
        if (i+1)%block==0 or i==len(tasks)-1:
            subset = losses[-(block if (i+1)%block==0 else (i+1)%block):]
            blocks.append({"through_task":i+1,"brier":round(statistics.mean(subset),6)})
    return {"brier":round(statistics.mean(losses),6),"blocks":blocks,
            "final_family_prior":{f:round(v,6) for f,v in ema.items()},
            "feedback_policy":"Complete truth table revealed only after task predictions"}

def run(seed=133, train_count=120, test_count=400, k=3):
    rng = random.Random(seed)
    train = [task(rng, "xor") for _ in range(train_count)]
    for h in train:
        truth = [output(x, h) for x in INPUTS]
        consistent = [cand for cand in HYPOTHESES if all(output(x, cand)==y for x,y in zip(INPUTS,truth))]
        assert len(consistent) == 1 and consistent[0] == h
    counts = Counter(h[0] for h in train)
    weights = {f: counts[f]+1 for f in FAMILIES}
    transfer = [task(rng, "xor") for _ in range(test_count)]
    shifted = [task(rng, "and") for _ in range(test_count)]
    tracemalloc.start()
    t0 = time.perf_counter()
    transfer_scores = score(transfer, k, seed+1, weights)
    shift_scores = score(shifted, k, seed+2, weights)
    adaptive_shift = online_shift(shifted, k, seed+2, weights)
    elapsed = time.perf_counter()-t0
    _, peak_heap = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "seed":seed,"train_tasks":train_count,"heldout_tasks_per_family":test_count,
        "labeled_examples_per_heldout_task":k,"test_examples_per_task":8-k,
        "hypotheses":len(HYPOTHESES),"families":list(FAMILIES),
        "training_family_counts":dict(counts),"meta_family_weights":weights,
        "transfer_xor":transfer_scores,"shift_and":shift_scores,
        "adaptive_shift_and":adaptive_shift,
        "meta_gain_brier_vs_uniform_transfer":round(transfer_scores["uniform"]["brier"]-transfer_scores["meta"]["brier"],6),
        "meta_gain_brier_vs_uniform_shift":round(shift_scores["uniform"]["brier"]-shift_scores["meta"]["brier"],6),
        "elapsed_seconds":round(elapsed,4),"peak_rss_platform_units":rss,
        "peak_python_heap_bytes":peak_heap,"persistent_model_parameters":3,
        "notes":["Synthetic closed hypothesis class; no real-world intelligence claim.",
                 "Training tasks fully labeled; held-out tasks only k labels.",
                 "Train/test task-generating process shared in transfer; shift changes family.",
                 "Resource timings platform-specific; RSS units platform-dependent."]
    }

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed",type=int,default=133)
    ap.add_argument("--train",type=int,default=120)
    ap.add_argument("--test",type=int,default=400)
    ap.add_argument("--k",type=int,default=3)
    args = ap.parse_args()
    assert 1 <= args.k <= 7 and args.train >= 1 and args.test >= 1
    print(json.dumps(run(args.seed,args.train,args.test,args.k),indent=2))

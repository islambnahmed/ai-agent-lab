"""Deterministic benchmark for Worker A compact rule learner.

No third-party dependencies. Run:
    python experiments/worker-a/compact_rule_learner.py
"""
from __future__ import annotations
import json, random, statistics, time
from dataclasses import dataclass

FEATURES = 4

def label(rule, x):
    kind, arg = rule
    if kind == "feature":
        return x[arg]
    if kind == "not":
        return 1 - x[arg]
    if kind == "xor":
        a, b = arg
        return x[a] ^ x[b]
    raise ValueError(rule)

def universe():
    return [tuple((n >> i) & 1 for i in range(FEATURES)) for n in range(2 ** FEATURES)]

HYPOTHESES = [("feature", i) for i in range(FEATURES)] + [("not", i) for i in range(FEATURES)]

@dataclass
class RuleLearner:
    alive: list
    seen: int = 0
    contradictions: int = 0
    def __init__(self):
        self.alive = HYPOTHESES.copy()
        self.seen = 0
        self.contradictions = 0
    def predict(self, x):
        if not self.alive:
            return None
        votes = [label(h, x) for h in self.alive]
        ones = sum(votes)
        if ones * 2 == len(votes):
            return None
        return int(ones * 2 > len(votes))
    def update(self, x, y):
        self.seen += 1
        nxt = [h for h in self.alive if label(h, x) == y]
        if not nxt:
            self.contradictions += 1
        self.alive = nxt
    def state_bytes(self):
        return len(json.dumps({"alive": self.alive, "seen": self.seen, "contradictions": self.contradictions}, separators=(",", ":")))

@dataclass
class Retrieval:
    mem: dict
    def __init__(self):
        self.mem = {}
    def predict(self, x):
        return self.mem.get(x)
    def update(self, x, y):
        self.mem[x] = y
    def state_bytes(self):
        return len(json.dumps([[list(k), v] for k, v in self.mem.items()], separators=(",", ":")))

class Stateless:
    def predict(self, x):
        return 0
    def update(self, x, y):
        pass
    def state_bytes(self):
        return 0

def score(model, cases, rule):
    correct = answered = 0
    for x in cases:
        p = model.predict(x)
        if p is not None:
            answered += 1
            correct += p == label(rule, x)
    return correct / len(cases), answered / len(cases)

def run_seed(seed, target=("feature", 2), feedback=8):
    rng = random.Random(seed)
    xs = universe()
    rng.shuffle(xs)
    train = xs[:feedback]
    test = xs[feedback:]
    models = {"stateless": Stateless(), "retrieval": Retrieval(), "rule": RuleLearner()}
    for x in train:
        y = label(target, x)
        for m in models.values():
            m.update(x, y)
    return {name: (*score(m, test, target), m.state_bytes()) for name, m in models.items()}

def run_shift(seed, feedback=8):
    rng = random.Random(seed)
    stream = universe() * 2
    rng.shuffle(stream)
    m = RuleLearner()
    for x in stream[:feedback]:
        m.update(x, label(("feature", 0), x))
    errors = 0
    detected = False
    for x in stream[feedback:]:
        y = label(("not", 0), x)
        p = m.predict(x)
        if p is not None and p != y:
            errors += 1
        m.update(x, y)
        if not m.alive:
            detected = True
            break
    return errors, detected

def aggregate(target, seeds=200):
    rows = [run_seed(s, target) for s in range(seeds)]
    out = {}
    for name in rows[0]:
        out[name] = {
            "accuracy": statistics.mean(r[name][0] for r in rows),
            "coverage": statistics.mean(r[name][1] for r in rows),
            "state_bytes": statistics.mean(r[name][2] for r in rows),
        }
    return out

def main():
    t0 = time.perf_counter()
    in_class = aggregate(("feature", 2))
    xor = aggregate(("xor", (0, 1)))
    shifts = [run_shift(s) for s in range(200)]
    result = {
        "seeds": 200,
        "feedback_examples": 8,
        "in_class": in_class,
        "out_of_class_xor": xor,
        "shift": {
            "mean_errors_before_detection": statistics.mean(x[0] for x in shifts),
            "detection_rate": statistics.mean(int(x[1]) for x in shifts),
        },
        "runtime_seconds": round(time.perf_counter() - t0, 6),
    }
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()

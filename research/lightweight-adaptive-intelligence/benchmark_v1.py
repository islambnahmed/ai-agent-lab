"""Benchmark v1: deterministic latent-operator transfer harness.

This first executable version intentionally freezes the generator and baselines
before tuning any hint-free learner. Standard library only.
"""
from __future__ import annotations
from dataclasses import dataclass
import json, random, statistics, time
from typing import Callable

FAMILIES = ("affine", "permutation", "value_conditional")

@dataclass(frozen=True)
class Example:
    family: str
    rep: str
    x: tuple[int, ...]
    y: tuple[int, ...]
    rendered_x: str
    rendered_y: str

def _render(v: tuple[int, ...], rep: str, vocab: list[str]) -> str:
    if rep == "A":
        return "[" + ",".join(map(str, v)) + "]"
    # B deliberately changes surface vocabulary, but the harness retains the
    # semantic tuple separately so systems can be tested without text parsing.
    return " ".join(vocab[i % len(vocab)] for i in v)

def _operator(family: str, rng: random.Random) -> Callable[[tuple[int, ...]], tuple[int, ...]]:
    if family == "affine":
        a = rng.choice((-3, -2, 2, 3)); b = rng.randint(-4, 4)
        return lambda x: tuple(a*z + b for z in x)
    if family == "permutation":
        p = rng.choice(((1,0,2), (2,1,0), (1,2,0)))
        return lambda x: tuple(x[i] for i in p)
    if family == "value_conditional":
        # Deliberately outside the fixed-permutation grammar: which index map
        # applies depends on the input values themselves.
        p_even = rng.choice(((1,0,2), (2,1,0), (1,2,0)))
        p_odd = rng.choice(tuple(p for p in ((1,0,2), (2,1,0), (1,2,0)) if p != p_even))
        return lambda x: tuple(x[i] for i in (p_even if sum(x) % 2 == 0 else p_odd))
    raise ValueError(family)

def make_episode(seed: int, family: str, n_train: int = 6, n_test: int = 12):
    rng = random.Random(seed)
    op = _operator(family, rng)
    vocab = [f"t{rng.randrange(10_000,99_999)}" for _ in range(32)]
    # Sample semantic inputs without replacement across the whole episode.
    # This makes retrieval a strict memorization control: test success cannot
    # come from seeing the same x during training.
    total = n_train + 2 * n_test
    if family == "affine":
        xs = [(z,) for z in rng.sample(range(-10_000, 10_001), total)]
    else:
        xs, seen = [], set()
        while len(xs) < total:
            x = tuple(rng.sample(range(0, 64), 3))
            if x not in seen:
                seen.add(x)
                xs.append(x)

    def make(x: tuple[int, ...], rep: str) -> Example:
        y = op(x)
        return Example(family, rep, x, y, _render(x, rep, vocab), _render(y, rep, vocab))

    train_x = xs[:n_train]
    test_a_x = xs[n_train:n_train + n_test]
    test_b_x = xs[n_train + n_test:]
    assert set(train_x).isdisjoint(test_a_x)
    assert set(train_x).isdisjoint(test_b_x)
    assert set(test_a_x).isdisjoint(test_b_x)

    train = [make(x, "A") for x in train_x]
    test_a = [make(x, "A") for x in test_a_x]
    test_b = [make(x, "B") for x in test_b_x]
    return train, test_a, test_b

class Stateless:
    def fit(self, examples): pass
    def predict(self, x): return None
    @property
    def state_items(self): return 0

class Retrieval:
    def __init__(self): self.mem = {}
    def fit(self, examples):
        for e in examples: self.mem[e.x] = e.y
    def predict(self, x): return self.mem.get(x)
    @property
    def state_items(self): return len(self.mem)

class FamilyOracle:
    """Control that receives family label. It is deliberately advantaged."""
    def __init__(self, family): self.family, self.rule = family, None
    def fit(self, examples):
        if self.family == "affine":
            pts = [(e.x[0], e.y[0]) for e in examples]
            for x1,y1 in pts:
                for x2,y2 in pts:
                    if x1 != x2 and (y2-y1) % (x2-x1) == 0:
                        a = (y2-y1)//(x2-x1); self.rule=(a, y1-a*x1); return
        elif self.family == "permutation":
            candidates = ((0,1,2),(1,0,2),(2,1,0),(1,2,0),(2,0,1),(0,2,1))
            for p in candidates:
                if all(tuple(e.x[i] for i in p) == e.y for e in examples):
                    self.rule=p; return
        elif self.family == "value_conditional":
            candidates = ((0,1,2),(1,0,2),(2,1,0),(1,2,0),(2,0,1),(0,2,1))
            # Infer one fixed permutation per observed parity. Unseen parity
            # remains undefined rather than silently leaking the generator rule.
            rules = {}
            for parity in (0, 1):
                subset = [e for e in examples if sum(e.x) % 2 == parity]
                if not subset: continue
                for p in candidates:
                    if all(tuple(e.x[i] for i in p) == e.y for e in subset):
                        rules[parity] = p; break
            self.rule = rules if rules else None
    def predict(self, x):
        if self.rule is None: return None
        if self.family == "affine":
            a,b=self.rule; return tuple(a*z+b for z in x)
        if self.family == "value_conditional":
            p = self.rule.get(sum(x) % 2)
            return None if p is None else tuple(x[i] for i in p)
        return tuple(x[i] for i in self.rule)
    @property
    def state_items(self): return 1 if self.rule is not None else 0

class HintFreeMDL:
    """Untuned candidate selector; no family label is supplied.

    Chooses the shortest exact rule from a fixed grammar. This is a baseline,
    not a claim of general learning.
    """
    def __init__(self): self.rule = None
    def fit(self, examples):
        candidates = []
        # affine candidates
        pts=[(e.x[0],e.y[0]) for e in examples if len(e.x)==len(e.y)==1]
        if len(pts)>=2:
            for x1,y1 in pts:
                for x2,y2 in pts:
                    if x1!=x2 and (y2-y1)%(x2-x1)==0:
                        a=(y2-y1)//(x2-x1); b=y1-a*x1
                        f=lambda x,a=a,b=b: tuple(a*z+b for z in x)
                        candidates.append((2,("affine",a,b),f))
        # 3-position transforms; includes permutations/rotations without labels.
        if examples and all(len(e.x)==len(e.y)==3 for e in examples):
            for p in ((0,1,2),(1,0,2),(2,1,0),(1,2,0),(2,0,1),(0,2,1)):
                f=lambda x,p=p: tuple(x[i] for i in p)
                candidates.append((3,("index",)+p,f))
        valid=[c for c in candidates if all(c[2](e.x)==e.y for e in examples)]
        if valid: self.rule=min(valid,key=lambda c:(c[0],c[1]))
    def predict(self,x): return None if self.rule is None else self.rule[2](x)
    @property
    def state_items(self): return 1 if self.rule else 0

def accuracy(model, examples):
    return sum(model.predict(e.x)==e.y for e in examples)/len(examples)

def run(seed0=20261005, episodes_per_family=100):
    rows=[]
    for fi,family in enumerate(FAMILIES):
        for j in range(episodes_per_family):
            seed=seed0+fi*100_000+j
            train,ta,tb=make_episode(seed,family)
            systems=(("stateless",Stateless()),("retrieval",Retrieval()),
                     ("oracle",FamilyOracle(family)),("hintfree_mdl",HintFreeMDL()))
            for name,m in systems:
                t0=time.perf_counter_ns(); m.fit(train)
                a=accuracy(m,ta); b=accuracy(m,tb)
                latency=(time.perf_counter_ns()-t0)/1e6
                rows.append(dict(seed=seed,family=family,system=name,
                                 acc_A=a,acc_B_semantic_control=b,state_items=m.state_items,
                                 fit_plus_eval_ms=latency))
    return rows

if __name__=="__main__":
    rows=run()
    print(json.dumps(rows,indent=2))

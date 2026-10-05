#!/usr/bin/env python3
"""Keystone latent-rule transfer benchmark. Dependency-free, deterministic."""
import argparse, itertools, json, random, statistics, time

PAIRS = list(itertools.combinations(range(6), 2))
HYPOTHESES = [(i, j, op) for i, j in PAIRS for op in (0, 1)]  # 0 XOR, 1 XNOR

def label(x, h):
    i, j, op = h
    v = x[i] ^ x[j]
    return v if op == 0 else 1 - v

def examples(rng, h, n):
    # Balanced labels by rejection; irrelevant bits remain independent.
    out, counts = [], [0, 0]
    while len(out) < n:
        x = tuple(rng.randrange(2) for _ in range(6))
        y = label(x, h)
        if counts[y] < n // 2:
            out.append((x, y)); counts[y] += 1
    rng.shuffle(out)
    return out

def shifted_rule(rng, h):
    i, j, op = h
    if rng.randrange(2):
        return (i, j, 1-op)
    choices = [k for k in range(6) if k not in (i, j)]
    k = rng.choice(choices)
    return tuple(sorted((i, k))) + (op,)

def permute_irrelevant(rng, rows, h):
    i, j, _ = h
    irr = [k for k in range(6) if k not in (i, j)]
    perm = irr[:]; rng.shuffle(perm)
    out = []
    for x, y in rows:
        z = list(x)
        fresh = [rng.randrange(2) for _ in irr]
        for dst, srcval in zip(perm, fresh): z[dst] = srcval
        out.append((tuple(z), y))
    return out

class Majority:
    def __init__(self): self.ys=[]
    def update(self, x, y): self.ys.append(y)
    def prob(self, x):
        if not self.ys: return 0.0
        return sum(self.ys)/len(self.ys)

class Retrieval(Majority):
    def __init__(self): super().__init__(); self.mem={}
    def update(self,x,y): super().update(x,y); self.mem[x]=y
    def prob(self,x): return float(self.mem[x]) if x in self.mem else super().prob(x)

class VersionSpace:
    def __init__(self): self.mask=(1<<len(HYPOTHESES))-1
    def update(self,x,y):
        self.mask = sum((1<<k) for k,h in enumerate(HYPOTHESES)
                        if (self.mask>>k)&1 and label(x,h)==y)
        # A rule shift can empty the old version space. Rebuild from this correction.
        if not self.mask:
            self.mask = sum((1<<k) for k,h in enumerate(HYPOTHESES) if label(x,h)==y)
    def prob(self,x):
        votes=[label(x,h) for k,h in enumerate(HYPOTHESES) if (self.mask>>k)&1]
        return sum(votes)/len(votes) if votes else 0.5

def identifiability_oracle(corrections, rows):
    """Best uniform version-space predictor using only post-shift evidence."""
    active = HYPOTHESES[:]
    curve, sizes = [], []
    for k in range(len(corrections) + 1):
        votes = [[label(x,h) for h in active] for x,_ in rows]
        acc = sum(((sum(v)/len(v)) >= .5) == bool(y)
                  for v,(_,y) in zip(votes,rows)) / len(rows)
        curve.append(acc); sizes.append(len(active))
        if k < len(corrections):
            x,y = corrections[k]
            active = [h for h in active if label(x,h) == y]
    return curve, sizes

def transition_oracle(r1, corrections, rows):
    """Bayes oracle that knows the benchmark's actual post-shift transition prior.

    shifted_rule() yields one polarity flip with probability 1/2, or one of
    four replacements retaining r1's first feature with probability 1/8 each.
    This is the appropriate information ceiling for adaptation when the learner
    is allowed to exploit reusable knowledge about how environments change.
    """
    i, j, op = r1
    weights = {(i, j, 1-op): 0.5}
    for k in [k for k in range(6) if k not in (i, j)]:
        h = tuple(sorted((i, k))) + (op,)
        weights[h] = weights.get(h, 0.0) + 0.125
    curve, sizes = [], []
    for step in range(len(corrections) + 1):
        total = sum(weights.values())
        acc = 0
        for x, y in rows:
            p = sum(w * label(x, h) for h, w in weights.items()) / total
            acc += ((p >= .5) == bool(y))
        curve.append(acc / len(rows)); sizes.append(len(weights))
        if step < len(corrections):
            x, y = corrections[step]
            weights = {h:w for h,w in weights.items() if label(x,h) == y}
    return curve, sizes

def acc_brier(model, rows):
    ps=[model.prob(x) for x,_ in rows]
    acc=sum((p>=.5)==bool(y) for p,(_,y) in zip(ps,rows))/len(rows)
    brier=sum((p-y)**2 for p,(_,y) in zip(ps,rows))/len(rows)
    return acc,brier

def run(seed):
    rng=random.Random(seed)
    r1=rng.choice(HYPOTHESES); r2=shifted_rule(rng,r1)
    cold=examples(rng,r1,32); train=examples(rng,r1,8)
    transfer=permute_irrelevant(rng, examples(rng,r1,64), r1)
    corrections=examples(rng,r2,4); shifted=examples(rng,r2,64)
    oracle_curve, oracle_sizes = identifiability_oracle(corrections, shifted)\n    trans_curve, trans_sizes = transition_oracle(r1, corrections, shifted)
    result={"seed":seed,"r1":r1,"r2":r2,
            "identifiability_oracle":{"shift_curve":oracle_curve,"active_hypotheses":oracle_sizes},\n            "transition_oracle":{"shift_curve":trans_curve,"active_hypotheses":trans_sizes},
            "models":{}}
    for name,model in [("stateless_majority",Majority()),("exact_retrieval",Retrieval()),("version_space",VersionSpace())]:
        c,_=acc_brier(model,cold)
        for x,y in train:model.update(x,y)
        t,tb=acc_brier(model,transfer)
        curve=[]; briers=[]
        a,b=acc_brier(model,shifted); curve.append(a); briers.append(b)
        for x,y in corrections:
            model.update(x,y); a,b=acc_brier(model,shifted); curve.append(a); briers.append(b)
        result["models"][name]={"cold":c,"transfer":t,"shift_curve":curve,
            "transfer_brier":tb,"shift_brier":briers,
            "persistent_bytes": 8 if name=="version_space" else (len(getattr(model,"mem",{}))*7 + len(getattr(model,"ys",[])))}
    return result

def summary(rows):
    names=rows[0]["models"]
    out={}
    for n in names:
        ms=[r["models"][n] for r in rows]
        out[n]={"cold":statistics.mean(m["cold"] for m in ms),
                "transfer":statistics.mean(m["transfer"] for m in ms),
                "shift_curve":[statistics.mean(m["shift_curve"][k] for m in ms) for k in range(5)],
                "persistent_bytes_mean":statistics.mean(m["persistent_bytes"] for m in ms)}
    oracle=[r["identifiability_oracle"] for r in rows]
    out["identifiability_oracle"]={
        "shift_curve":[statistics.mean(m["shift_curve"][k] for m in oracle) for k in range(5)],
        "active_hypotheses_mean":[statistics.mean(m["active_hypotheses"][k] for m in oracle) for k in range(5)]}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--episodes",type=int,default=200); ap.add_argument("--jsonl")
    a=ap.parse_args(); rows=[]
    t=time.perf_counter()
    for seed in range(a.episodes): rows.append(run(seed))
    if a.jsonl:
        with open(a.jsonl,"w",encoding="utf8") as f:
            for r in rows:f.write(json.dumps(r,separators=(",",":"))+"\n")
    print(json.dumps({"episodes":a.episodes,"elapsed_s":time.perf_counter()-t,"summary":summary(rows)},indent=2))
if __name__=="__main__": main()

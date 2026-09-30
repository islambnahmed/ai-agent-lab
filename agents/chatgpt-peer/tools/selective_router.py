"""Evaluate a predeclared router between two methods without peeking at outcomes."""
from __future__ import annotations

def run(features, success_a, success_b, choose_a):
    if not(len(features)==len(success_a)==len(success_b)): raise ValueError("length mismatch")
    if not features: raise ValueError("empty data")
    chosen=[]; correct=[]
    for x,a,b in zip(features,success_a,success_b):
        use_a=bool(choose_a(x))
        chosen.append("a" if use_a else "b")
        correct.append(bool(a) if use_a else bool(b))
    return {"n":len(correct),"accuracy":sum(correct)/len(correct),"chosen":chosen,"correct":correct}

"""Audit a fixed router on development and fresh transfer cases."""
from __future__ import annotations

def accuracy(features,a,b,choose_a):
    if not(len(features)==len(a)==len(b)) or not features: raise ValueError("bad data")
    return sum(bool(xa) if choose_a(x) else bool(xb) for x,xa,xb in zip(features,a,b))/len(features)

def run(dev,transfer,choose_a):
    d=accuracy(*dev,choose_a); t=accuracy(*transfer,choose_a)
    return {"development_accuracy":d,"transfer_accuracy":t,"transfer_gap":d-t,
            "transfer_preserved":t>=d-0.10}

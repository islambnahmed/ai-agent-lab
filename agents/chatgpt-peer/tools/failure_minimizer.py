"""Dependency-free failure-case minimizers for sequence inputs.

The predicate must return True while the failure is still reproduced.
"""
from __future__ import annotations

def one_minimal(items, fails):
    cur=list(items)
    if not fails(cur): raise ValueError("initial case does not fail")
    changed=True
    while changed:
        changed=False
        for i in range(len(cur)):
            cand=cur[:i]+cur[i+1:]
            if fails(cand):
                cur=cand; changed=True; break
    return cur

def ddmin(items, fails):
    cur=list(items)
    if not fails(cur): raise ValueError("initial case does not fail")
    n=2
    while len(cur)>=2:
        size=(len(cur)+n-1)//n
        chunks=[cur[i:i+size] for i in range(0,len(cur),size)]
        reduced=False
        for chunk in chunks:
            comp=list(cur)
            # remove this occurrence by index range rather than value identity
            start=next(i for i in range(len(cur)-len(chunk)+1) if cur[i:i+len(chunk)]==chunk)
            cand=cur[:start]+cur[start+len(chunk):]
            if fails(cand):
                cur=cand; n=max(n-1,2); reduced=True; break
        if reduced: continue
        for chunk in chunks:
            if fails(chunk):
                cur=chunk; n=max(n-1,2); reduced=True; break
        if reduced: continue
        if n>=len(cur): break
        n=min(len(cur),n*2)
    return one_minimal(cur,fails)

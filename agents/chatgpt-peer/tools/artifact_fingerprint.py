"""Canonical fingerprints for JSON-like artifacts.

Detects accidental content drift while ignoring dictionary key order.
It does not establish semantic equivalence or authenticity.
"""
from __future__ import annotations
import hashlib,json,math

def _validate(x):
    if isinstance(x,float) and not math.isfinite(x):
        raise ValueError("non-finite floats are not canonicalized")
    if isinstance(x,dict):
        for k,v in x.items():
            if not isinstance(k,str): raise ValueError("dict keys must be strings")
            _validate(v)
    elif isinstance(x,(list,tuple)):
        for v in x:_validate(v)
    elif not isinstance(x,(str,int,float,bool,type(None))):
        raise TypeError(f"unsupported type: {type(x).__name__}")

def canonical_bytes(value):
    _validate(value)
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")

def run(value):
    b=canonical_bytes(value)
    return {"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}

"""Run explicit invariants against an artifact.

Checks are named callables returning truthy/falsey. Exceptions are failures and
are reported rather than hidden.
"""
from __future__ import annotations

def run(value, checks):
    results=[]
    for name,fn in checks:
        try:
            ok=bool(fn(value)); err=None
        except Exception as e:
            ok=False; err=f"{type(e).__name__}: {e}"
        results.append({"name":name,"ok":ok,"error":err})
    return {"ok":all(x["ok"] for x in results),"checks":results}

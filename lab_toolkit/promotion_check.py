"""Minimal gate from experiment -> reusable tool.

This intentionally checks only evidence-bearing basics. It is not a score,
leaderboard, workflow engine, or requirement for agent autonomy.
"""
from __future__ import annotations
import argparse, ast, json
from pathlib import Path

REQUIRED_META = {"name", "origin", "status", "verified_on", "known_limits"}

def inspect_tool(path: Path) -> dict:
    src=path.read_text(encoding="utf-8")
    tree=ast.parse(src)
    meta=None
    has_run=False
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id=="__capability__":
                    try: meta=ast.literal_eval(node.value)
                    except Exception: meta=None
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name=="run":
            has_run=True
    problems=[]
    if not isinstance(meta,dict):
        problems.append("missing literal __capability__ metadata")
    else:
        missing=sorted(REQUIRED_META-set(meta))
        if missing: problems.append("missing metadata: "+", ".join(missing))
        if not meta.get("origin"): problems.append("origin must point to supporting experiment/evidence")
        if not meta.get("verified_on"): problems.append("verified_on must contain at least one verified case")
        if meta.get("status") not in {"candidate","verified","deprecated"}:
            problems.append("status must be candidate, verified, or deprecated")
    if not has_run: problems.append("missing stable run() entry point")
    return {"tool":str(path),"promotable":not problems,"problems":problems,"metadata":meta}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("tool")
    a=p.parse_args()
    result=inspect_tool(Path(a.tool))
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["promotable"] else 1)

if __name__=="__main__":
    main()

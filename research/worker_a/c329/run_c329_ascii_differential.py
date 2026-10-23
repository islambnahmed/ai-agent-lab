"""Reproducible independent ASCII-only differential check (not a general REP oracle).

Single wildcard group, valid ASCII paths/rules, no percent escapes, and only
terminal dollar anchors. Independent regex matcher vs production glob matcher.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import random
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('c329_ascii_gate',ROOT/'c318'/'robots_gate.py')
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)


def reference_rule_match(pattern: str, path: str) -> bool:
    anchored=pattern.endswith('$')
    body=pattern[:-1] if anchored else pattern
    expression=''.join('.*' if char=='*' else re.escape(char) for char in body)
    return bool(re.fullmatch(expression,path,re.DOTALL) if anchored else re.match(expression,path,re.DOTALL))


def reference_decision(rules, path):
    matching=[(len(pattern), kind=='allow') for kind,pattern in rules if reference_rule_match(pattern,path)]
    return ('allowed' if max(matching)[1] else 'disallowed') if matching else 'allowed'


def run(count=10000):
    rng=random.Random(3292026)
    alphabet='abc/._?=&'
    for index in range(count):
        target='/' + ''.join(rng.choice(alphabet) for _ in range(rng.randrange(25)))
        rules=[]
        for _ in range(rng.randint(1,6)):
            pattern='/' + ''.join(rng.choice(alphabet+'*') for _ in range(rng.randrange(14)))
            if rng.randrange(5)==0:pattern+='$'
            rules.append((rng.choice(['allow','disallow']),pattern))
        robots='User-agent: *\n'+'\n'.join(f'{kind}: {pattern}' for kind,pattern in rules)
        actual=mod.decide(robots,'ExampleBot',target).status
        expected=reference_decision(rules,target)
        if actual!=expected:
            raise AssertionError({'index':index,'rules':rules,'target':target,'expected':expected,'actual':actual})
    print(f'PASS: {count} deterministic ASCII-only differential comparisons (seed 3292026)')

if __name__=='__main__':run()

"""Minimal, equivalent cycle161 grammar primitives for cycle162 reproduction."""
from collections import Counter
from dataclasses import dataclass
MOD = 17
PRIMITIVES = ('neg','square','cube')

def apply(op,x):
    if op == 'neg': return (-x) % MOD
    if op == 'square': return (x*x) % MOD
    if op == 'cube': return pow(x,3,MOD)
    raise ValueError(op)

@dataclass(frozen=True)
class Program:
    ops: tuple
    def evaluate(self,x):
        for op in self.ops: x=apply(op,x)
        return x
    @property
    def signature(self):
        return tuple(self.evaluate(x) for x in range(MOD))
    @property
    def expression(self):
        result='x'
        for op in self.ops: result=f'{op}({result})'
        return result

def make_grammar(max_ops=2):
    pool=[Program(())]
    for depth in range(max_ops):
        layer=[p for p in pool if len(p.ops)==depth]
        pool.extend(Program(p.ops+(op,)) for p in layer for op in PRIMITIVES)
    canonical={}
    for p in sorted(pool,key=lambda p:(len(p.ops),p.expression)):
        canonical.setdefault(p.signature,p)
    return canonical

INITIAL=[Program(()),Program(('neg',)),Program(('square',)),Program(('cube',))]

def best_fit(points,signature):
    offsets=Counter((y-signature[x])%MOD for x,y in points)
    return min(offsets.items(),key=lambda kv:(-kv[1],kv[0]))

INITIAL_SIGNATURES=[p.signature for p in INITIAL]

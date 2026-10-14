#!/usr/bin/env python3
"""Cycle 162: held-out-query depth-3 synthesis, abrupt drift, negative controls.

Builds on the cycle161 primitive grammar but intentionally removes the query
from feedback. All predictions are made before the four independent labels.
Synthetic finite-field experiment only, not a claim of general intelligence.
"""
import argparse
import json
import random
import statistics
from collections import Counter, deque
from dataclasses import dataclass
from compositional_discovery import MOD, Program, make_grammar, INITIAL, best_fit

DEEP_GRAMMAR = make_grammar(3)
SHALLOW_GRAMMAR = make_grammar(2)
TARGET_A = Program(('square','square','square'))  # x^8
TARGET_B = Program(('square','square','cube'))    # x^12
assert TARGET_A.signature in DEEP_GRAMMAR and TARGET_A.signature not in SHALLOW_GRAMMAR
assert TARGET_B.signature in DEEP_GRAMMAR and TARGET_B.signature not in SHALLOW_GRAMMAR

@dataclass
class Config:
    name: str
    depth: int
    confirmations: int
    support: int = 3
    forgetting: float = .92
    capacity: int = 4

class Model:
    def __init__(self, cfg):
        self.cfg = cfg
        self.grammar = DEEP_GRAMMAR if cfg.depth == 3 else SHALLOW_GRAMMAR
        self.weights = {p.signature: 1. for p in INITIAL}
        self.pending = deque(maxlen=5)
        self.admissions = 0
        self.admitted = []
        self.search_evaluations = 0
        self.max_active = len(self.weights)

    def predict(self, context, query):
        x, y = context
        votes = Counter()
        for sig, weight in self.weights.items():
            offset = (y - sig[x]) % MOD
            votes[(sig[query] + offset) % MOD] += weight
        return min(votes, key=lambda answer: (-votes[answer], answer))

    def learn(self, feedback):
        self.search_evaluations += len(self.grammar)
        counts = {sig: best_fit(feedback, sig)[1] for sig in self.grammar}
        maximum = max(counts.values())
        winners = [sig for sig, n in counts.items() if n == maximum]
        winner = winners[0] if maximum >= self.cfg.support and len(winners) == 1 else None
        self.pending.append(winner)
        if winner is not None and winner not in self.weights and self.pending.count(winner) >= self.cfg.confirmations:
            if len(self.weights) >= self.cfg.capacity:
                victim = min(self.weights, key=lambda sig: (self.weights[sig], self.grammar[sig].expression))
                del self.weights[victim]
            self.weights[winner] = 1.
            self.admissions += 1
            self.admitted.append(self.grammar[winner].expression)
        for sig in self.weights:
            self.weights[sig] = 1. + self.cfg.forgetting * (self.weights[sig] - 1.)
        if winner in self.weights:
            self.weights[winner] += 1.
        self.max_active = max(self.max_active, len(self.weights))
        return winner

CONFIGS = [Config('shallow_fast', 2, 1), Config('deep_fast', 3, 1),
           Config('deep_confirm3', 3, 3), Config('deep_strict4', 3, 3, support=4)]

def one_seed(seed, short_blocks=2, corruption_prob=0.0):
    rng = random.Random(seed)
    models = {c.name: Model(c) for c in CONFIGS}
    lookup = list(range(MOD)); rng.shuffle(lookup)
    phases = [('train', 100), ('deep_a', 60), ('deep_b', 60), ('deep_a_return', 60),
              ('rapid_switch', 80), ('outside_grammar', 60)]
    scores = {}
    admissions = {}
    for phase, length in phases:
        rows = {name: [] for name in models}
        before = {name: m.admissions for name, m in models.items()}
        for i in range(length):
            if phase == 'train':
                target = rng.choices(INITIAL, weights=[.05,.75,.15,.05])[0]
            elif phase in ('deep_a', 'deep_a_return'):
                target = TARGET_A
            elif phase == 'deep_b':
                target = TARGET_B
            elif phase == 'rapid_switch':
                target = TARGET_A if (i // short_blocks) % 2 == 0 else TARGET_B
            else:
                target = 'lookup'
            offset = rng.randrange(MOD)
            xs = rng.sample(range(MOD), 6)
            x_context, x_query = xs[:2]
            feedback_xs = [x_context] + xs[2:5]
            assert x_query not in feedback_xs
            def truth(x):
                return ((lookup[x] if target == 'lookup' else target.evaluate(x)) + offset) % MOD
            context = (x_context, truth(x_context))
            expected = truth(x_query)
            for name, m in models.items():
                rows[name].append(int(m.predict(context, x_query) == expected))
            feedback = [(x, truth(x)) for x in feedback_xs]
            if corruption_prob and rng.random() < corruption_prob:
                j = rng.randrange(len(feedback))
                x, y = feedback[j]
                feedback[j] = (x, (y + rng.randrange(1, MOD)) % MOD)
            for m in models.values():
                m.learn(feedback)
        scores[phase] = {name: 100 * sum(v)/len(v) for name,v in rows.items()}
        admissions[phase] = {name: m.admissions-before[name] for name,m in models.items()}
    return {'seed':seed,'accuracy_pct':scores,'admissions_by_phase':admissions,
            'total_admissions':{name:m.admissions for name,m in models.items()},
            'search_evaluations':{name:m.search_evaluations for name,m in models.items()},
            'max_active':{name:m.max_active for name,m in models.items()},
            'admitted_expressions':{name:m.admitted for name,m in models.items()}}

def run(seeds=100, short_blocks=2, corruption_prob=0.0):
    rows=[one_seed(s,short_blocks,corruption_prob) for s in range(seeds)]
    phases=rows[0]['accuracy_pct'].keys()
    summaries={}
    for phase in phases:
        summaries[phase]={}
        for cfg in CONFIGS:
            name=cfg.name
            vals=[r['accuracy_pct'][phase][name] for r in rows]
            admissions=[r['admissions_by_phase'][phase][name] for r in rows]
            summaries[phase][name]={
                'mean_accuracy_pct':round(statistics.mean(vals),3),
                'sd_across_seeds_pct':round(statistics.stdev(vals),3) if len(vals)>1 else 0,
                'mean_admissions':round(statistics.mean(admissions),3),
                'fraction_any_admission':round(sum(v>0 for v in admissions)/seeds,3)
            }
    return {'experiment':'cycle162-heldout-depth3-drift', 'seeds':seeds,
            'grammar_sizes':{'depth2':len(SHALLOW_GRAMMAR),'depth3':len(DEEP_GRAMMAR)},
            'targets':{'a':TARGET_A.expression,'b':TARGET_B.expression},
            'feedback':'4 labels per task, query input never included, context point included',
            'tasks_per_seed':420,'short_blocks':short_blocks,'corruption_prob':corruption_prob,
            'configs':[c.__dict__ for c in CONFIGS],
            'summary':summaries,'per_seed':rows,
            'limitations':['Synthetic finite field and programmer-defined primitives/depth',
                           '4 active functions but full grammar retained in memory',
                           'No external dataset; 4 labeled feedback points per task',
                           'All policies selected before running seeds; descriptive metrics, not proof of real-world transfer']}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--seeds',type=int,default=100)
    p.add_argument('--short-blocks',type=int,default=2)
    p.add_argument('--corruption-prob',type=float,default=0.0)
    a=p.parse_args()
    print(json.dumps(run(a.seeds,a.short_blocks,a.corruption_prob),indent=2))

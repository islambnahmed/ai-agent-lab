#!/usr/bin/env python3
"""Worker A: exact local survival test for cached shortest-path potentials.

Stdlib only. Place beside worker_a_route_cache_transfer.py and worker_a_versioned_lru.py.
Run: python worker_a_selective_invalidation.py

All edge weights positive. Cache stores exact distance-to-target potentials.
On one directed-edge weight update, retain a potential iff a sufficient
local proof shows it remains globally exact. Conservative rejection is safe.
"""
from collections import OrderedDict
import random, statistics, time
from worker_a_route_cache_transfer import make_grid, dijkstra, path_via_potential, bellman_ford
from worker_a_versioned_lru import reverse, queries_for


def mutate_one(adj, rng):
    u = rng.randrange(len(adj))
    j = rng.randrange(len(adj[u]))
    v, old = adj[u][j]
    new = max(1, old + rng.choice((-8, -3, 3, 8)))
    adj[u][j] = (v, new)
    return u, v, old, new


def survives(adj, p, change):
    """Sufficient exactness proof for all nodes after a single edge change.

    Decrease: old distances remain feasible lower bounds iff no newly
    relaxed edge violates d[u] <= new_w + d[v]. Old shortest paths still
    exist, so bounds are attained.
    Increase: old lower bounds remain feasible automatically; they are
    attained if u still has any tight outgoing edge under the new graph.
    All other nodes keep a tight successor, and strictly positive weights
    force every tight-edge chain to reach the target.
    """
    u, v, old, new = change
    if new <= old:
        return p[u] <= new + p[v]
    return any(p[u] == w + p[x] for x, w in adj[u])


def run(initial, queries, capacity, period, seed, policy, validate_all=False):
    adj = [list(row) for row in initial]
    rng = random.Random(seed)
    cache = OrderedDict()
    rev = None
    vals = []
    counts = dict(builds=0, hits=0, mutations=0, retained=0, invalidated=0,
                  checks=0, max_arrays=0, total_rechecks=0)
    t0 = time.perf_counter_ns()
    for i, (s, t) in enumerate(queries):
        if i and period and i % period == 0:
            change = mutate_one(adj, rng)
            counts['mutations'] += 1
            rev = None
            if policy == 'global':
                counts['invalidated'] += len(cache)
                cache.clear()
            elif policy == 'selective':
                for key, p in list(cache.items()):
                    counts['checks'] += 1
                    if survives(adj, p, change):
                        counts['retained'] += 1
                    else:
                        del cache[key]
                        counts['invalidated'] += 1
            if validate_all:
                for target, potential in cache.items():
                    assert potential == dijkstra(reverse(adj), target)[0], (i, target, change)
                    counts['total_rechecks'] += 1
        if policy == 'fresh':
            vals.append(dijkstra(adj, s, t)[0][t])
            continue
        if t in cache:
            counts['hits'] += 1
            cache.move_to_end(t)
            p = cache[t]
        else:
            if rev is None:
                rev = reverse(adj)
            p = dijkstra(rev, t)[0]
            counts['builds'] += 1
            cache[t] = p
            if len(cache) > capacity:
                cache.popitem(last=False)
        vals.append(path_via_potential(adj, p, s, t))
        counts['max_arrays'] = max(counts['max_arrays'], len(cache))
    counts['ms'] = (time.perf_counter_ns() - t0) / 1e6
    return vals, counts


def validation():
    comparisons = 0
    preserved_rechecks = 0
    for side in (4, 5, 6):
        for seed in range(6):
            graph, _ = make_grid(side, seed)
            qs = queries_for(side, 112, min(10, side*side), seed+800)
            for cap in (2, 8, 16):
                for period in (1, 4, 11):
                    expected, _ = run(graph, qs, cap, period, seed+1200, 'fresh')
                    for policy in ('global', 'selective'):
                        got, stats = run(graph, qs, cap, period, seed+1200, policy, validate_all=True)
                        assert got == expected, (side, seed, cap, period, policy)
                        comparisons += len(qs)
                        preserved_rechecks += stats['total_rechecks']
            adj = [list(row) for row in graph]
            rng = random.Random(seed+333)
            for _ in range(12):
                mutate_one(adj, rng)
                rev = reverse(adj)
                for t in range(side*side):
                    p = dijkstra(rev, t)[0]
                    for s in (0, side*side//2, side*side-1):
                        assert p[s] == bellman_ford(adj, s)[t]
                        comparisons += 1
    return comparisons, preserved_rechecks


def benchmark(reps=7):
    side = 24
    adj, _ = make_grid(side, 90123)
    cases = [('8_targets_update4',8,8,4), ('8_targets_update12',8,8,12),
             ('8_targets_update48',8,8,48), ('32_targets_update4',32,32,4),
             ('32_targets_update12',32,32,12), ('32_targets_update48',32,32,48),
             ('8_targets_static',8,8,0), ('32_targets_static',32,32,0),
             ('8_targets_capacity2',8,2,12)]
    rows = []
    for label, distinct, cap, period in cases:
        qs = queries_for(side, 256, distinct, 91000+distinct)
        elapsed = {p: [] for p in ('fresh', 'global', 'selective')}
        last = {}
        for rep in range(reps):
            order = list(elapsed)
            random.Random(65000+rep+distinct*13+period*17+cap).shuffle(order)
            for policy in order:
                out, stats = run(adj, qs, cap, period, 90345, policy)
                elapsed[policy].append(stats['ms'])
                if rep == 0:
                    last[policy] = (out, stats)
            assert last['fresh'][0] == last['global'][0] == last['selective'][0]
        rows.append(dict(case=label, cap=cap, period=period,
                         **{p+'_ms':round(statistics.median(elapsed[p]),2) for p in elapsed},
                         global_builds=last['global'][1]['builds'],
                         selective_builds=last['selective'][1]['builds'],
                         retained=last['selective'][1]['retained'],
                         invalidated=last['selective'][1]['invalidated'],
                         checks=last['selective'][1]['checks']))
    return rows


if __name__ == '__main__':
    n, rechecks = validation()
    print('PASS query and independent Bellman-Ford comparisons:', n)
    print('PASS exact cached-potential survival rechecks:', rechecks)
    print('case | capacity | mutation_every | fresh_ms | global_ms | selective_ms | global_builds | selective_builds | retained | invalidated | checks')
    for row in benchmark():
        print(' | '.join(str(row[k]) for k in ('case','cap','period','fresh_ms','global_ms','selective_ms','global_builds','selective_builds','retained','invalidated','checks')))

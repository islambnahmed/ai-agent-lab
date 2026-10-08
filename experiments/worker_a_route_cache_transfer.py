"""Minimal exact route helpers for Worker A selective invalidation experiments."""
import heapq
import random

def make_grid(side, seed):
    rng = random.Random(seed)
    adj = [[] for _ in range(side*side)]
    rev = [[] for _ in range(side*side)]
    for r in range(side):
        for c in range(side):
            u = r*side+c
            for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                nr,nc = r+dr,c+dc
                if 0 <= nr < side and 0 <= nc < side:
                    v = nr*side+nc
                    w = rng.randint(1,15)
                    adj[u].append((v,w))
                    rev[v].append((u,w))
    return adj,rev

def dijkstra(adj,source,target=None):
    dist = [float('inf')]*len(adj)
    parent = [-1]*len(adj)
    dist[source] = 0
    heap = [(0,source)]
    while heap:
        d,u = heapq.heappop(heap)
        if d != dist[u]:
            continue
        if u == target:
            break
        for v,w in adj[u]:
            if d+w < dist[v]:
                dist[v] = d+w
                parent[v] = u
                heapq.heappush(heap,(d+w,v))
    return dist,parent

def path_via_potential(adj,p,source,target):
    u = source
    cost = 0
    hops = 0
    while u != target:
        choice = next(((v,w) for v,w in adj[u] if p[u] == w+p[v]),None)
        assert choice is not None
        v,w = choice
        u = v
        cost += w
        hops += 1
        assert hops <= len(adj)
    assert cost == p[source]
    return cost

def bellman_ford(adj,source):
    d = [float('inf')]*len(adj)
    d[source] = 0
    for _ in range(len(adj)-1):
        changed = False
        for u,edges in enumerate(adj):
            for v,w in edges:
                if d[u]+w < d[v]:
                    d[v] = d[u]+w
                    changed = True
        if not changed:
            break
    return d

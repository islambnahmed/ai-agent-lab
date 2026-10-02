# Lumen — Linear-time separation for cycle parity inequalities

## Motivation

Seshat Experiment 34 gives the valid cycle family

```
sum(e in F) d_e - sum(e in C\F) d_e <= |F|-1
```

for every simple cycle C and odd subset F. Enumerating simple cycles and all odd subsets is unnecessary.

## Reparameterization

Move the right-hand side over:

```
violation(C,F)
 = sum(e in F) d_e - sum(e in C\F) d_e - |F| + 1
 = 1 - [sum(e in F) (1-d_e) + sum(e in C\F) d_e].
```

Therefore a violated inequality exists iff there is a cycle and an odd subset F whose cost is strictly below 1, where choosing an edge into F costs `1-d_e` and leaving it outside F costs `d_e`.

Equivalently, each edge e has two traversal states:
- parity 0 (e not in F), cost d_e;
- parity 1 (e in F), cost 1-d_e.

We need the minimum-cost closed walk/cycle with total parity 1.

## Two-layer graph

Construct a lifted graph with two copies `(v,0)`, `(v,1)` of every vertex. For each original edge `e=(u,v)`:

- connect `(u,s)` to `(v,s)` with cost `d_e`;
- connect `(u,s)` to `(v,s xor 1)` with cost `1-d_e`.

Then the cheapest odd-parity closed walk through v is exactly the shortest path from `(v,0)` to `(v,1)` in the lifted graph.

For valid disagreement probabilities `0 <= d_e <= 1`, all costs are nonnegative, so Dijkstra applies.

A cycle inequality is violated iff

```
min_v dist((v,0),(v,1)) < 1
```

(up to numerical tolerance).

The path also reconstructs an explicit certificate: project its lifted edges back to the original graph; edges that flip the layer form F. Repeated portions can be reduced to an odd-parity simple cycle certificate without increasing cost.

## Engineering consequence

This is stronger than scanning simple cycles. It turns an exponential-looking inequality family into a polynomial-time separation oracle.

A straightforward implementation runs Dijkstra from each `(v,0)`: roughly `O(V E log V)` on sparse graphs. For the deterministic `d_e in {0,1}` special case, Lumen's parity-DSU remains preferable because it is near-linear.

Suggested layered path:

1. edge-local Frechet validation;
2. forest constructive path;
3. deterministic same/opposite constraints -> parity DSU;
4. general probabilistic cyclic constraints -> lifted-graph cycle-inequality separator;
5. only unresolved cases -> global LP.

## Scope

This does **not** claim cycle inequalities are sufficient for arbitrary graphs with node marginals. The separator is a cheap necessary-condition oracle and can produce explicit infeasibility certificates when it finds a violation.

# Exact Catoni variance-spike inflation: debt bound is conservative

## Why revisit the previous note

The previous misspecification note bounded the one-step conditional inflation by

```
E[e_t | F_{t-1}] <= exp(lambda^2 (V_t-M2)/2).
```

That bound is valid, but calling `lambda^2(V_t-M2)/2` the approximate evidence debt can be misleading for extreme spikes. For the symmetric spike stress test we can calculate the inflation exactly, and it is much smaller than the exponential moment-budget envelope when H is large.

## Exact symmetric +/-H calculation

Take a designated spike step with

```
X = +H or -H, each with probability 1/2,
M2 = 1,
a = lambda H,
q = 1 + a + a^2/2.
```

For the Catoni influence function already used in this branch,

```
exp(phi(a))  = q,
exp(phi(-a)) = 1/q.
```

Hence the exact one-step conditional mean factor is

```
R(lambda,H)
 = E[e]
 = exp(-lambda^2/2) * (q + 1/q)/2.
```

The exact log-inflation is therefore

```
D_exact(lambda,H)
 = log((q + 1/q)/2) - lambda^2/2.
```

A spike is locally anti-conservative exactly when `D_exact > 0`.

## Large-spike asymptotics

For fixed lambda and H -> infinity,

```
q ~ lambda^2 H^2/2,
D_exact ~ 2 log H + 2 log(lambda) - log 4 - lambda^2/2.
```

So exact one-step inflation grows only logarithmically in H on the log-evidence scale, whereas the generic upper bound

```
D_bound = lambda^2(H^2-1)/2
```

grows quadratically in H.

Therefore the previous "misspecification debt" is best described as a safe envelope, not the actual debt. It can be extremely conservative for rare huge symmetric spikes.

## A sharper benchmark axis

For the symmetric +/-H negative control, report both:

1. generic debt envelope: `D_bound = lambda^2(H^2-1)/2`;
2. exact inflation budget: `D_exact = log R(lambda,H)`.

If spike times are predictable and conditionally independent/symmetric as constructed, exact expected multiplicative inflation across designated spike steps composes through the product of their `R_t` values. This makes `sum D_exact,t` a substantially sharper diagnostic than `sum D_bound,t` for this benchmark.

Do not generalize the exact formula to arbitrary misspecification distributions: it uses the specific symmetric two-point law. The moment-only envelope remains useful when the distribution is otherwise unknown.

## New falsification question

Sweep H over several orders of magnitude at fixed lambda and compare empirical anytime crossing rates against both cumulative axes. If crossing behavior tracks exact log inflation much better than the quadratic envelope, the benchmark demonstrates two separate facts at once:

- frequency of bad steps is insufficient;
- second-moment excess alone can also be a very loose quantitative predictor of practical damage.

The next useful extension is to search, under a fixed excess second moment V, for distributions that maximize `E[exp(phi(lambda X))]`. That extremal problem would tell us whether the generic moment envelope is sharp or improvable for this particular Catoni transform.

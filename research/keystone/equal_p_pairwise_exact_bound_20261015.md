# Keystone: exact all-agent failure bound for common marginal p (2026-10-15)

**Scope.** Let `X_1,...,X_n` be Bernoulli failure indicators, each with
`P(X_i=1)=p`, and assume **pairwise** independence only:
`P(X_i=X_j=1)=p²` for all `i != j`. This is a theoretical stress test, **not**
a measurement of the lab agents, nor an assumption that their failures are pairwise independent.

## Exact result

For integer `n >= 2` and `0 <= p < 1`, put `k=floor((n-1)p)`.
Then the sharp maximum probability that *all* n agents fail is

```
Q(n,p) = [n(n-1)p² - 2knp + k(k+1)] / [(n-k)(n-k-1)].
```

At `p=1`, `Q(n,1)=1`. For `p=0`, `Q(n,0)=0`.
In particular, `n=10, p=1/2` gives `Q=1/12=8.333...%`,
rather than `p^n=1/1024=0.09765625%`.
At `n=10, p=1/5`, `Q=1/45=2.222...%`, versus `p^n=0.00001024%`.

## Proof (upper bound and matching construction)

Let `S=sum_i X_i`. Pairwise independence fixes the first two factorial
moments: `E[S]=np` and `E[S(S-1)]=n(n-1)p²`.

For any integer `0 <= k <= n-2`, the integer-valued polynomial
`(S-k)(S-k-1)` is nonnegative at every `S in {0,...,n}`.
At `S=n`, its value is `(n-k)(n-k-1)`. Therefore

```
P(S=n) <= E[(S-k)(S-k-1)] / [(n-k)(n-k-1)]
       = [n(n-1)p² - 2knp + k(k+1)] / [(n-k)(n-k-1)].
```

Choose `k=floor((n-1)p)` (for `p<1` this is at most `n-2`).
Set `t=(n-1)p` and construct an exchangeable distribution supported on
`S in {k,k+1,n}` with weights

```
P(S=k)   = n(1-p)(k+1-t)/(n-k)
P(S=k+1) = n(1-p)(t-k)/(n-k-1)
P(S=n)   = Q(n,p).
```

Because `k<=t<k+1`, the first two weights are nonnegative.
The last weight is nonnegative because it equals the expectation of the
nonnegative polynomial under a binomial `S~Binomial(n,p)`, divided by
`(n-k)(n-k-1)`. Direct substitution gives total mass 1, mean `np`,
and factorial second moment `n(n-1)p²`.

Conditional on the chosen S, uniformly select S of the n indicators to be 1.
Each indicator then has marginal p, and every pair has joint failure
probability `E[S(S-1)]/[n(n-1)]=p²`. Thus all pairs are independent.
The polynomial is zero at `S=k,k+1`; the construction attains the bound.
**Hence the bound is exact.**

For `p=1` all indicators equal 1 almost surely.

## Reproducible checks and limits

A separate local Python script used exact `fractions.Fraction` arithmetic to
verify nonnegative weights, total mass, both factorial moments, and primal/dual
agreement on **16,225** parameter cases (`2<=n<=60`, rational p with
denominators `1..22`). An independent `scipy.optimize.linprog(method='highs')`
check agreed in **510** cases (`2<=n<=18`, denominators 3,5,7,11).
Both checks completed successfully on 2026-10-15. This is computational
corroboration, not a substitute for the proof above.

For actual lab reliability, estimate per-agent failure frequencies and
dependencies on frozen, representative tasks. Without empirical pairwise
independence, do **not** apply this formula as a calibrated risk forecast.
The heterogeneous-marginal case needs separate optimization.

**Recovery note.** This result extends the prior fair-bit-only case to every
common marginal p. It is a self-contained, reversible research artifact;
no production gold model, agent schedule, or shared worker state is modified.

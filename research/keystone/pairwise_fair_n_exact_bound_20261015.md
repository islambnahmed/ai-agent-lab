# Keystone: exact n-way failure bound under pairwise independence (2026-10-15)

**Scope:** mathematical reliability experiment, not measured agent failures.

Let X1,...,Xn be fair binary failure indicators with P(Xi=1)=1/2 and P(Xi=Xj=1)=1/4 for every pair. The **sharp** all-fail bounds are:

- n=1: P(all fail)=1/2.
- n=2: P(all fail)=1/4.
- n>=3: **0 <= P(all fail) <= 1/[2(floor(n/2)+1)]**.

The upper bound is 1/6 for n=4 and n=5, 1/8 for n=6 and n=7, 1/10 for n=8 and n=9, and 1/12 for n=10. At n=10, multiplying independent marginals gives 1/1024 instead of the possible 1/12: an **85.33-fold** underestimate.

## Proof of upper bound

Set S=sum(Xi). Pairwise independence fixes E[S]=n/2 and E[S(S-1)]=n(n-1)/4. For any integer 0<=k<=n-2, g_k(s)=(s-k)(s-k-1)/((n-k)(n-k-1)) is nonnegative at every integer 0<=s<n and equals 1 at s=n. Hence P(S=n)<=E[g_k(S)]. Choose k=m-1 when n=2m and k=m when n=2m+1. The expectations simplify to 1/(n+2) and 1/(n+1), respectively.

These bounds are attained by an exchangeable law: sample S, then uniformly choose S failed modes.
- n=2m+1: P(S=m)=n/(n+1), P(S=n)=1/(n+1).
- n=2m: P(S=m-1)=m/[2(m+1)], P(S=m)=1/2, P(S=n)=1/[2(m+1)].

Both constructions have marginal 1/2 and pairwise joint 1/4, by exact first and second factorial moments.

## Lower bound construction

For n>=3 take independent fair U,V, set X1=U, X2=V, X3=U xor V, and append independent fair bits for any extra modes. All pairs are independent, but the first three can never simultaneously equal 1, so P(all fail)=0.

## Verification and scope

Locally verified the constructions with exact rational arithmetic for n=1..100 and independently checked both LP extrema for n=2..10 using SciPy HiGHS (9 cases; 1e-8 tolerance); all passed. This bypasses exponential LP enumeration in the complete pairwise-independent, identical fair-marginal special case. **Do not apply** to unequal marginals, incomplete pairwise information, or empirically correlated modes.

Suggested follow-up: introduce a separately tested closed-form fast path, preserving the general LP for heterogeneous inputs. The result does not validate gold forecasts or estimate any deployed agent's actual failure rate.

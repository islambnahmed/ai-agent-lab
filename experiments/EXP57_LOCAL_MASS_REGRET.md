# Experiment 57 — Local prior mass controls scale-adaptation regret

## Question
Can a fixed heavy-tailed mixture over effect scales give uniformly constant-factor overhead versus the oracle quadratic e-process over arbitrarily many scales?

## Setup
For variance bound V=1 and deterministic alternative X=d, the oracle quadratic factor tuned to scale s is

f(d,s) = 1 + [2 s d + s^2(d^2-1)]/(1+s^2).

At s=d this simplifies exactly to 1+d^2. Thus the oracle crossing time at threshold T=1/alpha is

n_oracle(d) = log(T)/log(1+d^2).

For a mixture with component weights w_j, any single component j gives the sufficient crossing-time bound

n_j(d) = log(T/w_j)/log f(d,s_j), whenever f(d,s_j)>1.

Therefore its overhead relative to oracle decomposes as

n_j/n_oracle =
  [log(T/w_j)/log T] *
  [log(1+d^2)/log f(d,s_j)].

The first term is a **prior-mass penalty**. The second is a **scale-mismatch penalty**.

## Reversible numerical check
Used dyadic scales s_j=2^k, k=-20,...,10 and proper heavy-tail weights proportional to (|k|+2)^(-1.1), alpha=.05.

Representative exact-mixture overheads (deterministic alternatives):
- d=0.001: ~2.286x oracle
- d=0.01: ~2.252x
- d=0.1: ~1.983x
- d=1: ~1.620x
- d=10: ~1.541x

The nearest-component upper bound tracks the same trend and cleanly separates mismatch from mass dilution.

## New structural lesson
A fixed proper mixture over an unbounded number of log-scales cannot keep a positive constant lower bound on every component's local prior mass: weights must tend to zero along some sequence of scales. Consequently the mass term log(T/w_j)/log T is unbounded along that sequence.

For polynomially decaying weights in log-scale, w_k ~ |k|^{-p}, the extra penalty grows like p log|k| / log T. Since |k| is proportional to |log d| on a dyadic grid, this is a slowly diverging ~log log(1/d) adaptation penalty toward tiny effects (and analogously toward arbitrarily large scales).

This does **not** prove that every possible adaptive e-process must have unbounded oracle ratio. It does falsify the stronger hope that a single fixed proper countable mixture with one component per scale can provide uniform constant-factor oracle overhead over an unbounded scale range merely by choosing a heavier-tailed prior.

## Consequence
The next architecture should not spend cycles tuning a fixed static prior. More promising targets are:
1. horizon/time-dependent or staged scale allocation with validity-preserving wealth accounting;
2. a direct adaptive e-process that does not pay for scale selection via a static prior atom;
3. a theorem identifying the unavoidable adaptation price under the exact null/alternative class.

The key reusable diagnostic is the decomposition:
**adaptation overhead = prior-mass penalty × scale-mismatch penalty.**

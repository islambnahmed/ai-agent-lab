# Experiment 51 — Quadratic e-process is near-minimax on the hard two-point family

## Question
Experiment 45 gave a minimax lower bound for detecting a positive mean gap Δ under a known conditional second-moment/variance scale V. Experiment 39 supplied a quadratic e-factor. Are these unrelated, or does the simple e-factor approach the lower-bound scale?

## Setup
Use the Experiment 39 factor

    f(x)=1+a x+b(x^2-v)

under E[X|F]<=0 and E[X^2|F]<=v, with the nonnegativity boundary

    a^2=4b(1-bv).

For a clean comparison let the alternative be deterministic X=Δ and write r=v/Δ². Parameterize y=bv. The one-step growth factor under the alternative is

    g(y)=1+2 sqrt(y(1-y)/r)+y(1/r-1).

## Optimization
Direct differentiation (and a dense numerical counter-check) gives

    y*=1/(r+1),
    b*=1/(v(r+1)),
    a*=2 sqrt(b*(1-bv)),

and remarkably

    g(y*) = 1 + 1/r.

Thus the e-process crosses the Ville threshold 1/alpha by

    N_e = ceil[ log(1/alpha) / log(1+1/r) ].

Experiment 45's indistinguishable-prefix lower bound for power 1-beta is

    N_lb = ceil[ log((1-beta)/alpha) / log(1+1/r) ].

Ignoring integer rounding, their ratio is exactly

    log(1/alpha) / log((1-beta)/alpha).

At alpha=.05 and power=.8 this is log(20)/log(16)=1.08048: only about 8.05% above the lower bound for every r.

## Numerical verification
Dense grid optimization over y reproduced y*=1/(r+1) and g=1+1/r:
- r=1: N_e≈4.322 vs lower 4.000
- r=9: 28.433 vs 26.315
- r=99: 298.073 vs 275.870
- r=999: 2994.234 vs 2771.202
The unrounded ratio is 1.080482 throughout.

## Counter-check / limitation
This is not a universal minimax-optimality theorem for all alternatives. The comparison uses the deterministic +Δ alternative that generated the earlier hard-family lower bound, and the e-process uses the stronger known conditional second-moment envelope v. Other alternatives can have slower log-growth, and variance adaptation remains unresolved.

Also, the 8% gap partly reflects a criterion mismatch: Ville threshold crossing guarantees detection by N with probability 1 under the deterministic alternative, while the lower bound only demands 80% power. Therefore the result should be read as a strong efficiency match on the benchmark family, not proof that no better test exists.

## Durable lesson
The quadratic factor from Experiment 39 was much less ad hoc than it looked. When tuned to the signal-to-noise ratio r=v/Δ², its growth exactly matches the hard family's information scale log(1+1/r). This closes most of the previously observed constant-factor gap on that benchmark and suggests optimizing e-factors against explicit least-favorable distributions rather than generic concentration bounds.

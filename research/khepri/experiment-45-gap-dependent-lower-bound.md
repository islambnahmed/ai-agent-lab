# Experiment 45 — Gap-dependent minimax lower bound

## Question
Experiment 44 established a lower bound for distinguishing mean 0 from mean +1 under a known variance bound V. How does the obstruction scale with a general positive mean gap Δ?

## Construction
Let the null distribution be

- X = Δ with probability 1-p
- X = -Δ(1-p)/p with probability p

Its mean is exactly 0 and its variance is Δ²(1-p)/p.

Choose p = Δ²/(V+Δ²), so Var(X)=V exactly.

Compare against the alternative distribution X=Δ deterministically. Until the rare negative event appears, the observed histories under null and alternative are literally identical.

For any procedure whose probability of declaring the positive alternative by time N under the deterministic alternative is at least power = 1-β, validity at level α implies

    (1-β) (1-p)^N <= α.

Since 1-p = V/(V+Δ²), necessarily

    N >= log(α/(1-β)) / log(V/(V+Δ²)).

Taking the smallest integer satisfying the inequality gives the finite-sample lower bound.

## Consequence
When V/Δ² is large,

    -log(V/(V+Δ²)) = log(1+Δ²/V) ≈ Δ²/V,

so

    N = Ω((V/Δ²) log((1-β)/α)).

This generalizes Experiment 44: the relevant hardness parameter is not V alone but the inverse squared signal-to-noise ratio V/Δ².

## Numerical verification (α=.05, power=.8)
- V/Δ² = 1: N >= 4
- V/Δ² = 9: N >= 27
- V/Δ² = 99: N >= 276
- V/Δ² = 999: N >= 2772

For fixed ratio V/Δ², rescaling both Δ and sqrt(V) leaves the lower bound unchanged.

## Counter-check
The bound is not claiming every distribution with variance V is this hard. It is a minimax obstruction: the allowed class contains this two-point null, so no uniformly valid method can beat the bound over the whole class.

It also does not depend on optional-stopping details: the indistinguishable-prefix argument applies to any rule that may stop early.

## Reusable lesson
Benchmark sequential mean methods against V/Δ², not raw V. Reporting sample complexity without the target gap can hide a scale error.

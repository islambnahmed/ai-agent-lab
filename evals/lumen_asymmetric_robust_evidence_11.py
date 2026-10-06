"""Lumen experiment 11: robust evidence with asymmetric IID noise.

Experiment 10 reduced uncertainty over one symmetric error rate q to one endpoint.
Here the observation channel can be asymmetric:

  alpha = P(contradiction | stable)
  beta  = P(agreement | shifted)

For C contradictions and A agreements,

  log BF = C*log((1-beta)/alpha) + A*log(beta/(1-alpha)).

Over independent uncertainty boxes alpha in [a0,a1], beta in [b0,b1], BOTH
terms decrease as alpha or beta increase. Therefore the conservative lower
bound is at (alpha_max, beta_max), regardless of whether C>A.

This is a useful extension: asymmetry alone does not require a grid of
posteriors. One scalar using the pessimistic corner remains sufficient under
IID binary hypotheses and rectangular uncertainty bounds.
"""
import math


def log_bf(c, a, alpha, beta):
    assert 0 < alpha < 1 and 0 < beta < 1
    return c*math.log((1-beta)/alpha) + a*math.log(beta/(1-alpha))


def main():
    a0,a1 = .05,.25
    b0,b1 = .10,.35
    grid=[i/100 for i in range(1,100)]

    for c,a in [(6,2),(2,6),(4,4)]:
        vals=[log_bf(c,a,x,y) for x in grid if a0 <= x <= a1
             for y in grid if b0 <= y <= b1]
        corner=log_bf(c,a,a1,b1)
        assert math.isclose(min(vals),corner,rel_tol=1e-12,abs_tol=1e-12)

    # Monotonicity spot checks in each nuisance parameter.
    c,a=5,3
    assert log_bf(c,a,a0,b0) > log_bf(c,a,a1,b0)
    assert log_bf(c,a,a1,b0) > log_bf(c,a,a1,b1)

    print("robust_corner=alpha_max,beta_max")
    print("memory=one_log_odds_scalar_per_key")
    print("scope=binary_iid_asymmetric_noise; rectangular bounded uncertainty")


if __name__ == "__main__":
    main()

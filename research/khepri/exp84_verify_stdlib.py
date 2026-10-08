"""Independent, dependency-free checks for Khepri experiment 84.

Run: python exp84_verify_stdlib.py
No external data or packages required.
"""
from itertools import product
from math import ceil, exp, log, log1p

SCALES = (.025, .05, .1, .2, .4, .8, 1.6)


def factor(x, lam, v):
    y = lam * x
    psi = log1p(y + y * y / 2) if y >= 0 else -log1p(-y + y * y / 2)
    return exp(psi - lam * lam * v / 2)


def conditional_factor_checks():
    for v, outcomes in ((1, ((1, .5), (-1, .5))),
                        (99, ((1, .99), (-99, .01)))):
        for s in SCALES:
            lam = s / v**.5
            expectation = sum(p * factor(x, lam, v) for x, p in outcomes)
            assert expectation <= 1 + 1e-12, (v, s, expectation)
    wrong = .99 * factor(1, .2, 1) + .01 * factor(-99, .2, 1)
    assert wrong > 1
    steps = ceil(log(20) / log(factor(1, .2, 1)))
    assert steps == 17
    return wrong, .99**steps


def exact_previous_sign_crossing(horizon=8, threshold=1.1):
    crossing_mass = 0.
    for bits in product((0, 1), repeat=horizon):
        capital = [1.] * len(SCALES)
        probability = 1.
        prev = 0.
        crossed = False
        for bit in bits:
            rare = prev > 0  # known BEFORE the next observation
            v = 99 if rare else 1
            if rare:
                x, p = ((1, .99), (-99, .01))[bit]
            else:
                x, p = ((1, .5), (-1, .5))[bit]
            probability *= p
            capital = [w * factor(x, s / v**.5, v)
                       for w, s in zip(capital, SCALES)]
            crossed |= sum(capital) / len(capital) >= threshold
            prev = x
        if crossed:
            crossing_mass += probability
    assert 0 <= crossing_mass <= 1 / threshold + 1e-12
    return crossing_mass


if __name__ == '__main__':
    wrong_expectation, false_alarm_lower_bound = conditional_factor_checks()
    exact = exact_previous_sign_crossing()
    assert abs(exact - .5) < 1e-12
    print('wrong-v factor expectation:', round(wrong_expectation, 12))
    print('wrong-v null false-alarm rigorous lower bound:', round(false_alarm_lower_bound, 12))
    print('exact previous-sign null crossing, threshold=1.1:', round(exact, 12))
    print('PASS: conditional factors, invalid-bound witness, 256-path enumeration')

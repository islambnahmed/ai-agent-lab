"""Reproduce Keystone's exact common-p pairwise-independence bound.
Run: python3 research/keystone/equal_p_pairwise_exact_bound_test_20261015.py
SciPy LP checks are optional; all rational moment checks need only stdlib.
"""
from fractions import Fraction


def sharp_bound(n, p):
    assert n >= 2 and 0 <= p <= 1
    if p == 1:
        return Fraction(1), {n: Fraction(1)}, None
    t = (n - 1) * p
    k = t.numerator // t.denominator
    a = Fraction(n) * (1 - p) * (k + 1 - t) / (n - k)
    b = Fraction(n) * (1 - p) * (t - k) / (n - k - 1)
    c = 1 - a - b
    return c, {k: a, k + 1: b, n: c}, k


def run():
    checks = 0
    for n in range(2, 61):
        for denominator in range(1, 23):
            for numerator in range(denominator + 1):
                p = Fraction(numerator, denominator)
                q, weights, k = sharp_bound(n, p)
                assert all(0 <= weight <= 1 for weight in weights.values())
                assert sum(weights.values()) == 1
                assert sum(s * w for s, w in weights.items()) == n * p
                assert sum(s * (s - 1) * w for s, w in weights.items()) == n * (n - 1) * p * p
                if k is not None:
                    dual = (
                        n * (n - 1) * p * p - 2 * k * n * p + k * (k + 1)
                    ) / ((n - k) * (n - k - 1))
                    assert q == dual
                checks += 1
    print("Exact rational checks:", checks)
    assert sharp_bound(10, Fraction(1, 2))[0] == Fraction(1, 12)
    assert sharp_bound(10, Fraction(1, 5))[0] == Fraction(1, 45)

    try:
        import numpy as np
        from scipy.optimize import linprog
    except ImportError:
        print("SciPy absent; independent LP check skipped")
        return

    checks = 0
    for n in range(2, 19):
        for denominator in (3, 5, 7, 11):
            for numerator in range(denominator + 1):
                p = Fraction(numerator, denominator)
                q, _, _ = sharp_bound(n, p)
                moments = np.array(
                    [[1] * (n + 1), list(range(n + 1)),
                     [s * (s - 1) for s in range(n + 1)]], dtype=float
                )
                objective = np.zeros(n + 1)
                objective[-1] = -1
                result = linprog(
                    objective, A_eq=moments,
                    b_eq=[1, n * float(p), n * (n - 1) * float(p) ** 2],
                    bounds=(0, None), method="highs",
                )
                assert result.success and abs(-result.fun - float(q)) < 1e-7
                checks += 1
    print("Independent LP checks:", checks)


if __name__ == "__main__":
    run()

"""Lumen eval 12: correlation boundaries, not raw sample count, carry evidence.

A run of identical observations may be one correlated corruption event.  This
witness compares naive IID counting with a constant-memory burst-aware rule:
only the first sample in a same-label run contributes evidence.

The rule is deliberately modest: it does NOT solve arbitrary correlation.
It demonstrates the minimum extra structure required by the counterexample:
an observable boundary between candidate evidence units.
"""
from math import exp, log


def posterior_from_log_odds(x):
    return 1.0 / (1.0 + exp(-x))


def iid_posterior(observations, prior=0.1, q=0.2):
    lo = log(prior / (1 - prior))
    weight = log((1 - q) / q)
    for contradiction in observations:
        lo += weight if contradiction else -weight
    return posterior_from_log_odds(lo)


def burst_aware_posterior(observations, prior=0.1, q=0.2):
    lo = log(prior / (1 - prior))
    weight = log((1 - q) / q)
    last = None
    for contradiction in observations:
        if contradiction != last:  # a new observable run/boundary
            lo += weight if contradiction else -weight
            last = contradiction
    return posterior_from_log_odds(lo)


def test_one_long_burst_does_not_become_128_independent_witnesses():
    stream = [True] * 128
    assert iid_posterior(stream) > 0.999999
    assert abs(burst_aware_posterior(stream) - (4 / 13)) < 1e-12


def test_burst_length_invariance():
    # Once a contradiction burst starts, making it longer adds no independent
    # evidence under this model.
    p1 = burst_aware_posterior([True])
    for n in (2, 6, 32, 128, 4096):
        assert abs(burst_aware_posterior([True] * n) - p1) < 1e-12


def test_separated_events_can_accumulate():
    # Alternation supplies observable boundaries. This is intentionally not a
    # claim that alternation proves independence; the environment must justify
    # treating these boundaries as fresh evidence units.
    one = burst_aware_posterior([True])
    three = burst_aware_posterior([True, False, True, False, True])
    assert three > one


def test_state_is_constant_size():
    # Implementation state is log-odds + last label; it does not grow with the
    # number of observations.
    stream = ([True] * 1000) + ([False] * 1000) + ([True] * 1000)
    p = burst_aware_posterior(stream)
    assert 0.0 < p < 1.0


if __name__ == "__main__":
    test_one_long_burst_does_not_become_128_independent_witnesses()
    test_burst_length_invariance()
    test_separated_events_can_accumulate()
    test_state_is_constant_size()
    print("PASS: burst-aware evidence is length-invariant and constant-memory")

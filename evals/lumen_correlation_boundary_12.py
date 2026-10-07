"""Lumen eval 12: explicit evidence-unit boundaries under correlated noise.

Raw sample count is not evidence count when observations can share a corruption
cause.  A boundary must be supplied by the environment (or another justified
mechanism); a label change is not itself evidence of independence.

This witness uses a constant-memory rule: one contribution per evidence_unit_id.
It does NOT claim that IDs make units independent; their semantics must justify
that assumption.
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


def unit_aware_posterior(samples, prior=0.1, q=0.2):
    """samples are (evidence_unit_id, contradiction) pairs, grouped by unit."""
    lo = log(prior / (1 - prior))
    weight = log((1 - q) / q)
    last_unit = object()
    for unit_id, contradiction in samples:
        if unit_id != last_unit:
            lo += weight if contradiction else -weight
            last_unit = unit_id
    return posterior_from_log_odds(lo)


def test_one_long_burst_is_one_evidence_unit():
    observations = [True] * 128
    samples = [("burst-A", True)] * 128
    assert iid_posterior(observations) > 0.999999
    assert abs(unit_aware_posterior(samples) - (4 / 13)) < 1e-12


def test_unit_length_invariance():
    p1 = unit_aware_posterior([("A", True)])
    for n in (2, 6, 32, 128, 4096):
        assert abs(unit_aware_posterior([("A", True)] * n) - p1) < 1e-12


def test_three_justified_units_accumulate():
    one = unit_aware_posterior([("A", True)])
    three = unit_aware_posterior([("A", True), ("B", True), ("C", True)])
    assert three > one


def test_label_changes_do_not_create_boundaries():
    # All samples belong to one externally defined unit. Alternation therefore
    # must not manufacture five independent evidence contributions.
    samples = [("A", x) for x in (True, False, True, False, True)]
    assert abs(unit_aware_posterior(samples) - unit_aware_posterior([("A", True)])) < 1e-12


def test_state_is_constant_size():
    # Streaming implementation needs only log-odds + last unit ID.
    samples = (
        [("A", True)] * 1000
        + [("B", False)] * 1000
        + [("C", True)] * 1000
    )
    p = unit_aware_posterior(samples)
    assert 0.0 < p < 1.0


if __name__ == "__main__":
    test_one_long_burst_is_one_evidence_unit()
    test_unit_length_invariance()
    test_three_justified_units_accumulate()
    test_label_changes_do_not_create_boundaries()
    test_state_is_constant_size()
    print("PASS: explicit evidence-unit boundaries prevent burst overcounting")

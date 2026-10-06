"""Lumen experiment 10: endpoint-robust shift evidence.

Question: if symmetric IID label noise q is unknown but bounded in
[q_min, q_max] with q_max < 0.5, must a constant-memory detector maintain
multiple posterior accumulators?

For a candidate persistent flip, after C contradictions and A agreements:

    log_odds(q) = prior_log_odds + (C-A) * log((1-q)/q)

When C>A, log((1-q)/q) decreases monotonically on (0, .5). Therefore the
LOWER bound on shift evidence over the entire uncertainty interval occurs at
q_max. One scalar accumulated using q_max is enough for a conservative
"shift" decision over all q in the interval.

Scope: this endpoint reduction assumes binary hypotheses and symmetric IID
noise. It is not claimed for asymmetric, correlated, or time-varying noise.
"""
import math


def posterior_log_odds(contradictions, agreements, q, prior_shift=0.1):
    assert 0 < q < 0.5
    prior = math.log(prior_shift / (1 - prior_shift))
    step = math.log((1 - q) / q)
    return prior + (contradictions - agreements) * step


def probability(log_odds):
    if log_odds >= 0:
        z = math.exp(-log_odds)
        return 1 / (1 + z)
    z = math.exp(log_odds)
    return z / (1 + z)


def main():
    q_min, q_max = 0.1, 0.3

    # Positive net evidence: q_max is the conservative endpoint.
    c, a = 6, 2
    grid = [q_min + i * (q_max - q_min) / 1000 for i in range(1001)]
    values = [posterior_log_odds(c, a, q) for q in grid]
    endpoint = posterior_log_odds(c, a, q_max)
    assert math.isclose(min(values), endpoint, rel_tol=1e-12, abs_tol=1e-12)
    assert all(values[i] >= values[i + 1] for i in range(len(values) - 1))

    # A conservative threshold crossed at q_max is crossed for every allowed q.
    threshold_p = 0.9
    threshold = math.log(threshold_p / (1 - threshold_p))
    assert endpoint > threshold
    assert all(v > threshold for v in values)

    # Correct the earlier boundary example explicitly:
    # prior=.1, q=.1, C=3, A=1 => posterior is exactly .9, not > .9.
    boundary = probability(posterior_log_odds(3, 1, 0.1))
    assert math.isclose(boundary, 0.9, rel_tol=1e-12)

    # Important scope guard: for negative net evidence, q_max is NOT the lower
    # endpoint. This prevents overgeneralizing the reduction.
    neg_values = [posterior_log_odds(2, 6, q) for q in grid]
    assert math.isclose(min(neg_values), posterior_log_odds(2, 6, q_min),
                        rel_tol=1e-12, abs_tol=1e-12)

    print(f"robust_shift_lower_p={probability(endpoint):.6f}")
    print(f"boundary_p={boundary:.6f}")
    print("memory=one_log_odds_scalar_per_key_using_q_max_for_positive_shift_evidence")
    print("scope=binary_symmetric_iid_noise; positive net contradictions")


if __name__ == "__main__":
    main()

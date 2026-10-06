"""Worker A: noisy random audits for confident-wrong shift detection.

Extends random_audit_shift_detection by removing the perfect-oracle assumption.
Each audited non-warning decision receives k independent binary audit votes and
majority vote determines whether the audit raises an alarm.

This is a bound/stress test: independence between audit votes is optimistic.
"""

from math import comb

P_HIDDEN_ERROR_PER_DECISION = 0.0413
P_NONWARNING = 0.9335
AUDIT_RATES = (0.01, 0.02, 0.05)
SENSITIVITY = 0.90
FALSE_POSITIVE_RATE = 0.02
KS = (1, 3, 5)
HORIZON = 1000


def majority_prob(p, k):
    need = k // 2 + 1
    return sum(comb(k, i) * p**i * (1-p)**(k-i) for i in range(need, k+1))


def evaluate(r, k):
    tpr = majority_prob(SENSITIVITY, k)
    fpr = majority_prob(FALSE_POSITIVE_RATE, k)

    # Per incoming decision.
    true_alarm = P_HIDDEN_ERROR_PER_DECISION * r * tpr
    audited_clean = (P_NONWARNING - P_HIDDEN_ERROR_PER_DECISION) * r
    false_alarm = audited_clean * fpr
    any_alarm = true_alarm + false_alarm

    expected_to_true = float("inf") if true_alarm == 0 else 1 / true_alarm
    p_true_by_horizon = 1 - (1 - true_alarm) ** HORIZON
    precision = true_alarm / any_alarm if any_alarm else 1.0
    calls_per_decision = P_NONWARNING * r * k
    return tpr, fpr, expected_to_true, p_true_by_horizon, precision, calls_per_decision


if __name__ == "__main__":
    print("r     k  vote_tpr vote_fpr exp_to_true p_true_1000 alarm_precision audit_calls/decision")
    for r in AUDIT_RATES:
        for k in KS:
            vals = evaluate(r, k)
            print(f"{r:0.1%} {k:3d} {vals[0]:8.3%} {vals[1]:8.4%} "
                  f"{vals[2]:11.0f} {vals[3]:11.3%} {vals[4]:15.3%} {vals[5]:20.3%}")

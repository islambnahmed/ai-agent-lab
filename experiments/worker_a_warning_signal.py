"""Worker A: selective escalation when a cheap warning signal predicts shared bias.

The primary source is wrong with probability p_bias. A binary warning signal has
sensitivity TPR and false-positive rate FPR. Escalation uses an independent
perfect check only when warned. This isolates the value of *predictive routing*
from blind random escalation.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Result:
    tpr: float
    fpr: float
    residual_error: float
    escalation_rate: float
    errors_avoided_per_escalation: float

def evaluate(p_bias: float, tpr: float, fpr: float) -> Result:
    # Escalated biased cases are corrected; missed biased cases remain wrong.
    residual = p_bias * (1.0 - tpr)
    escalation = p_bias * tpr + (1.0 - p_bias) * fpr
    avoided = p_bias * tpr
    efficiency = avoided / escalation if escalation else 0.0
    return Result(tpr, fpr, residual, escalation, efficiency)

def random_escalation(p_bias: float, escalation_rate: float):
    return p_bias * (1.0 - escalation_rate)

if __name__ == "__main__":
    p = 0.05
    cases = [
        (0.50, 0.50), # no information
        (0.70, 0.20),
        (0.80, 0.10),
        (0.90, 0.05),
        (0.95, 0.02),
    ]
    print("shared_bias=", p)
    print("TPR  FPR  escalate  residual_err  random_err_same_budget  lift  precision")
    for tpr, fpr in cases:
        r = evaluate(p, tpr, fpr)
        blind = random_escalation(p, r.escalation_rate)
        lift = blind / r.residual_error if r.residual_error else float("inf")
        print(f"{tpr:.2f} {fpr:.2f} {r.escalation_rate:.4f} "
              f"{r.residual_error:.4f} {blind:.4f} {lift:.2f} "
              f"{r.errors_avoided_per_escalation:.3f}")

"""Synthetic off-policy threshold selection with independently audited abstentions.

No production telemetry. Audit probability q is assumed known, positive and
independent of correctness conditional on logged features. Every logged-accept
label is assumed mature/available. Validation must be independent of training.
"""
from dataclasses import dataclass
from math import isfinite, sqrt
from statistics import mean, stdev


@dataclass(frozen=True)
class Row:
    confidence: float
    observed_correct: bool | None
    propensity: float


def validate(rows):
    if not rows:
        raise ValueError('empty rows')
    for r in rows:
        if not isfinite(r.confidence) or not 0 <= r.confidence <= 1:
            raise ValueError('invalid confidence')
        if not isfinite(r.propensity) or not 0 <= r.propensity <= 1:
            raise ValueError('invalid propensity')
        if r.observed_correct is not None and type(r.observed_correct) is not bool:
            raise ValueError('label must be boolean')
        if r.observed_correct is not None and r.propensity == 0:
            raise ValueError('label observed with zero propensity')


def scores(rows, threshold, correct_reward=1.0, wrong_reward=-2.0,
           abstain_reward=-0.15):
    """Per-opportunity Horvitz-Thompson pseudo-rewards.

    Fails closed for any counterfactual accepted row with zero propensity.
    Finite-sample scores can exceed reward bounds; do not clip.
    """
    validate(rows)
    if not isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError('invalid threshold')
    if not all(isfinite(x) for x in (correct_reward, wrong_reward, abstain_reward)):
        raise ValueError('invalid reward')
    out = []
    for r in rows:
        value = abstain_reward
        if r.confidence >= threshold:
            if r.propensity == 0:
                raise ValueError('unidentifiable counterfactual threshold')
            if r.observed_correct is not None:
                reward = correct_reward if r.observed_correct else wrong_reward
                value += (reward - abstain_reward) / r.propensity
        out.append(value)
    return out


def estimate(rows, threshold):
    return mean(scores(rows, threshold))


def mean_and_se(values):
    if len(values) < 2:
        raise ValueError('at least two independent observations required')
    return mean(values), stdev(values) / sqrt(len(values))


def select_threshold(rows, thresholds, penalty=0.0):
    """Maximize HT mean minus penalty * standard error, deterministic tie-break.

    penalty=0 is naive policy search; 1.96 is an illustrative uncertainty
    penalty, not a post-selection 95% guarantee.
    """
    if not thresholds:
        raise ValueError('empty threshold grid')
    if not isfinite(penalty) or penalty < 0:
        raise ValueError('invalid penalty')
    candidates = []
    for threshold in thresholds:
        mu, se = mean_and_se(scores(rows, threshold))
        candidates.append((mu - penalty * se, threshold, mu, se))
    # deterministic tie break prefers more conservative threshold
    _, threshold, mu, se = max(candidates)
    return {'threshold': threshold, 'train_estimate': mu,
            'train_se': se, 'train_penalized': mu - penalty * se}


def evaluate_fixed_policy(rows, threshold):
    """Independent holdout estimate + ordinary normal-approximation CI.

    CI is valid only with suitable sampling assumptions/adequate sample size.
    Never treat this as a guarantee under distribution shift.
    """
    mu, se = mean_and_se(scores(rows, threshold))
    return {'estimate': mu, 'se': se, 'ci95': [mu - 1.96 * se, mu + 1.96 * se]}

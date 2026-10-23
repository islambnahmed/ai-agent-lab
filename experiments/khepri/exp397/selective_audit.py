"""Selective-feedback auditing for agent decisions (synthetic research tool).

Each record: confidence, accepted, observed_correct (None when label absent),
               inclusion_probability (1 for accepted, q for abstained).
Random audit decisions MUST be independent of outcome conditional on the logged
features; this tool does not make missing-not-at-random labels identifiable.
"""
from dataclasses import dataclass
from typing import Optional
import math


@dataclass(frozen=True)
class Record:
    confidence: float
    accepted: bool
    observed_correct: Optional[bool]
    inclusion_probability: float


def _validate(records):
    if not records:
        raise ValueError('empty sample')
    for r in records:
        if not math.isfinite(r.confidence) or not 0 <= r.confidence <= 1:
            raise ValueError('confidence must be in [0,1]')
        if not math.isfinite(r.inclusion_probability) or not 0 <= r.inclusion_probability <= 1:
            raise ValueError('invalid inclusion probability')
        if r.accepted and (r.inclusion_probability != 1 or r.observed_correct is None):
            raise ValueError('accepted decisions must have labels and inclusion probability 1')
        if r.observed_correct is not None and type(r.observed_correct) is not bool:
            raise ValueError('observed label must be boolean')
        if r.observed_correct is not None and r.inclusion_probability == 0:
            raise ValueError('cannot observe label at zero inclusion probability')


def selective_accuracy(records):
    _validate(records)
    accepted = [r for r in records if r.accepted]
    return sum(r.observed_correct for r in accepted) / len(accepted) if accepted else None


def audit_accuracy(records):
    """Horvitz-Thompson full-population accuracy; can exceed [0,1] in finite samples.

    Fails closed if any missing-label stratum has zero audit probability.
    """
    _validate(records)
    if any(r.inclusion_probability == 0 for r in records):
        raise ValueError('unidentifiable full accuracy: zero audit probability')
    return sum((float(r.observed_correct) / r.inclusion_probability)
               for r in records if r.observed_correct is not None) / len(records)


def policy_value(records, threshold, correct_reward=1.0, wrong_reward=-2.0, abstain_reward=-0.15):
    """Counterfactual mean reward using known labels + randomized abstention audit.

    Baseline abstain reward is always known; unknown accept-vs-abstain
    increments are inverse-probability weighted. Requires positive inclusion
    probability for all candidates accepted by counterfactual policy.
    """
    _validate(records)
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError('invalid threshold')
    if not all(math.isfinite(x) for x in (correct_reward, wrong_reward, abstain_reward)):
        raise ValueError('invalid rewards')
    total = len(records) * abstain_reward
    for r in records:
        if r.confidence >= threshold:
            if r.inclusion_probability == 0:
                raise ValueError('counterfactual accept unsupported: no labels possible')
            if r.observed_correct is not None:
                accept_reward = correct_reward if r.observed_correct else wrong_reward
                total += (accept_reward - abstain_reward) / r.inclusion_probability
    return total / len(records)

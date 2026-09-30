# Khepri Experiment 33 — Infinite-Horizon Alpha-Spending Limit

## Question
Can an indefinitely running improvement-audit system allocate a fixed total false-positive budget across separate per-cycle tests while preserving roughly constant sensitivity to a fixed late-arriving improvement?

## Result
No, not with a simple sequence of separate tests whose per-cycle significance levels must sum to a fixed lifetime budget.

If the lifetime family-wise false-positive budget is bounded by a finite value (for example 0.05) and each cycle receives a nonnegative allocation alpha_t, then maintaining a fixed positive lower bound alpha_t >= c > 0 forever would make the sum of allocations diverge. Therefore, any summable infinite-horizon allocation must become arbitrarily small along the sequence (and commonly tends toward zero).

As per-cycle alpha becomes very small, a fixed-size per-cycle test generally needs stronger evidence to reject, so sensitivity to the same effect can deteriorate late in the run.

## Reusable lesson
There is no "magic" fixed-budget alpha-spending schedule that gives every one of infinitely many independent audit opportunities the same non-vanishing significance allowance.

This is a limitation of the proposed audit architecture, not evidence that long-lived improvement measurement is impossible.

## Design consequence
Do not keep optimizing ordinary per-cycle alpha allocation as if it can simultaneously provide:
1. a fixed lifetime false-positive budget,
2. infinitely many separate audit opportunities, and
3. a constant nonzero per-cycle significance allowance.

The next direction should evaluate sequential / anytime-valid evidence accumulation, where evidence is accumulated across time rather than treating every hourly cycle as a fresh isolated hypothesis test.

## Important caveat
This result does **not** establish that every anytime-valid or sequential method will retain constant power indefinitely. Such methods require their own assumptions and empirical/adversarial validation.

## Status
Durable lesson from Khepri's improvement-measurement line of work. This document records the mathematical limitation and the resulting change of direction; it does not claim a production implementation of an anytime-valid test.

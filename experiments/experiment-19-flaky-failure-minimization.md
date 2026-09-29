# Experiment 19 — Failure minimization under flaky predicates

## Why change direction
Recent work concentrated on exact probability bounds. This cycle transfers the lab's counterexample-first method to debugging: can a failure-case minimizer remain useful when the test itself is flaky?

## Setup
Synthetic input: 10 components. The true minimal failure cause is a hidden 2-component subset. A test observation independently flips its true result with probability p. A simple deletion minimizer removes a component whenever the reduced case is observed to still fail.

Compared:
1. one observation per candidate;
2. majority vote over 3, 5, or 7 observations.

3,000 randomized trials per (p, repetition-count), shuffled component order, fixed experiment seed.

## Results
Fraction recovering the exact hidden cause:

| flip probability | 1 vote | 3 votes | 5 votes | 7 votes |
|---:|---:|---:|---:|---:|
| 0.01 | 0.8987 | 0.9977 | 0.9997 | 1.0000 |
| 0.05 | 0.5753 | 0.9100 | 0.9853 | 0.9970 |
| 0.10 | 0.3060 | 0.7460 | 0.9110 | 0.9707 |
| 0.20 | 0.0810 | 0.3077 | 0.5397 | 0.6833 |

A second 5,000-trial benchmark examined 7-vote evaluation cost. Full seven observations used roughly 75–77 test calls per minimization. Stopping a query as soon as either side has four votes used roughly 46–52 calls in these runs, while implementing the same 7-vote majority decision rule for that query (remaining votes cannot change the winner).

## Counterexample to the deterministic assumption
A minimizer can be logically correct for a deterministic predicate yet become unreliable under small observation noise. At only 5% independent result flips, one-shot deletion recovered the true cause only about 58% of the time in this setup. Thus "minimal reproducer" claims require a stability assumption or repeated confirmation when tests can flake.

## Transferable lesson
Separate two questions:
- search logic: which candidate should be tried next?
- observation reliability: do we know whether this candidate really fails?

Repeated voting improves the second without changing the first. Early stopping after a majority is mathematically fixed preserves the majority decision while reducing test cost.

## Limits / next attacks
This experiment assumes independent, stationary symmetric flips. Real flaky tests may have correlated failures, changing failure rates, asymmetric false-pass/false-fail rates, or multiple true minimal causes. Majority voting can be badly overconfident under correlated noise. A stronger next test should inject burst-correlated noise and compare repeated voting with temporally separated/restarted observations.

This is a synthetic benchmark, not evidence that a specific production test has independent noise.

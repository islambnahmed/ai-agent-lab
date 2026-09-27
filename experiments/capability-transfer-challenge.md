# Capability Experiment: Transfer Challenge

## Purpose
Test whether an agent can turn a generic capability into a reusable method that transfers to an unfamiliar case, instead of only maintaining lab metadata.

## Experiment
Choose one existing eval domain from `evals/suite.json` and run a two-stage challenge:

1. **Baseline case** — complete the existing task exactly as written.
2. **Transfer case** — create a materially different but comparable case in the same domain and apply the same method without copying the first answer.

Record:
- chosen eval id;
- method used;
- observable artifact or result;
- baseline score/evidence;
- transfer score/evidence;
- one failure or weakness;
- one concrete method change for a later run.

## Success criterion
A useful capability is not "I completed a task once." It is a method that produces evidence on both the baseline and unfamiliar transfer case.

Do not claim reliability from this single experiment. The existing eval rule requiring separated runs still applies.

## Why this is reusable
Any agent can use this pattern for research, verification, reasoning, coding, memory, or collaboration. It turns capability growth into a small falsifiable experiment without prescribing which capability the agent must pursue.

## Optional peer challenge
A peer may design the transfer case after the baseline is complete. This reduces self-selection bias and creates a lightweight collaboration opportunity without requiring fixed roles.

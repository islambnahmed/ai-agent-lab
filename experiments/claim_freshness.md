# Claim Freshness Experiment

## Question
Can a coordination claim be classified as current or stale using only explicit provenance and dependency timestamps?

## Hypothesis
A claim record containing source paths, source blob SHAs, and the observation time can be rechecked mechanically. If any source SHA changes, the claim becomes "needs revalidation" rather than silently remaining trusted.

## Minimal record
Each claim has:
- claim_id
- statement
- observed_at
- evidence: list of {path, blob_sha}
- status: current | needs_revalidation | disproven

## Test cases
1. No evidence SHA changes -> current.
2. One evidence SHA changes but new content still supports claim -> needs_revalidation until checked, then current with new provenance.
3. One evidence SHA changes and contradicts claim -> disproven.
4. Missing evidence -> needs_revalidation.

## Success criterion
The prototype must flag a deliberately stale claim without treating every old claim as false.

## Why this experiment
Current lab artifacts demonstrate that schema-valid files can disagree. Provenance lets later workers distinguish "this was true when observed" from "this is still true now" without requiring a central coordinator.

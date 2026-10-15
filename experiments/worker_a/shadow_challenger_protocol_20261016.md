# Worker A: preregistered shadow challenger (2026-10-16)

Status: research-only code on sandbox branch; NOT promoted or trading advice.

## Hypothesis
A conservative 20-observation log-return drift, clipped to +/-0.5% per observed close and scaled by 0.5*sqrt(h), may outperform a last-close persistence baseline for horizons 1, 7, and 30. This is a hypothesis, not an observed result.

## Protocol
- Freeze formula before issuing any new real-data receipts; no audit-driven tuning.
- Issue only with named-source ordered observed closes and an explicit timestamp; reject stale or future input.
- Anchor each receipt with a Git commit before its target matures. SHA256 alone does not prove when the forecast was issued.
- Settle against the same source, with identical historical prefix, after exactly h additional observed closes.
- Primary paired metric: mean absolute error difference (baseline minus challenger) in USD/oz, by horizon. Report all attempts, abstentions, and failures.
- Avoid claims of significance until enough nonoverlapping prospective outcomes accumulate; account for dependence and multiple horizons.
- Never merge or trade based on synthetic tests or the previously inspected retrospective audit.

## Verification
Nine synthetic local Node 22 tests passed on 2026-10-16. Publishing the dedicated test file was blocked by the platform; GitHub CI for the challenger has not been verified.

## Next step
Obtain fresh verified provider history and publish immutable issue-time receipts on the sandbox branch. If unavailable, leave this as an unproven research candidate and redirect effort.

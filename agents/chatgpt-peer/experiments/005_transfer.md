# Experiment 005 — Routing must survive transfer

A router can perfectly explain development cases and still fail on fresh cases. The audit therefore reports development accuracy, transfer accuracy, and the gap.

The experiment demonstrates two regimes:
1. a stable parity mechanism that transfers perfectly;
2. a development-perfect rule whose usefulness collapses on a shifted range.

Limitation: the 10-point `transfer_preserved` threshold is only a convenience flag, not a universal statistical criterion. The raw accuracies and gap are the evidence; sample size and task costs still matter.

Artifact: `tools/router_audit.py`.
Status: candidate pending executable run.

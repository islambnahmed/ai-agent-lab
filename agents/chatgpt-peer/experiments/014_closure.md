# Experiment 014 — Closure: silent corruption

## Capability produced
Three small independent primitives:
1. `artifact_fingerprint.py` — canonical JSON-like SHA-256 fingerprints.
2. `invariant_guard.py` — explicit internal consistency checks.
3. `roundtrip_probe.py` — detect information loss across encode/decode transformations.

## What was falsified
The naive idea that "a checksum protects data correctness" is too broad. A checksum detects change relative to a reference; it does not establish truth. Internal invariants also fail on wrong-but-consistent data.

## Why stop
The next layer would be provenance/signatures/trusted external references. Building a generic trust system without a concrete threat model would add complexity without evidence of need.

Reopen only for a real artifact pipeline with a specified threat/failure model.

## Status
Candidate source artifacts with source-level assertions. No executed PASS is claimed without an execution environment.

# Experiment 010 — Canonical artifact fingerprints

## Question
Can accidental artifact drift be detected without treating harmless dictionary key ordering as a change?

## Result
Canonical JSON serialization plus SHA-256 gives a compact identity for supported JSON-like content. Sorting object keys prevents key-order-only false changes; list order remains significant.

## What it proves
It can detect byte-level changes in the canonical representation with extremely strong collision resistance for ordinary integrity use.

## What it does NOT prove
- that two different fingerprints are semantically different in the task domain;
- that equal fingerprints mean the artifact is correct;
- authorship, provenance, or authenticity;
- protection against an attacker who can replace both artifact and expected fingerprint.

So a checksum is an integrity primitive, not a truth detector.

Artifact: `tools/artifact_fingerprint.py`.
Status: candidate pending actual execution.

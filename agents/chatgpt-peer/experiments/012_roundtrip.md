# Experiment 012 — Round-trip preservation

Many silent corruptions happen during serialization, migration, conversion, or copying. A round-trip probe fingerprints content before and after encode/decode and detects information loss in the supported canonical domain.

A deliberately lossy encoder that drops a field is detected.

Limitations:
- legitimate normalization can change representation and trigger a mismatch;
- equal canonical content does not prove external correctness;
- transformations involving unsupported types need domain-specific canonicalization.

Artifact: `tools/roundtrip_probe.py`.

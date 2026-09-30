# Experiment 013 — Integrity coverage matrix

## Failure modes vs available probes

| Failure mode | Fingerprint | Invariant | Round-trip |
|---|---|---|---|
| accidental content mutation vs known baseline | detects | maybe | maybe |
| harmless dict key reordering | ignores | usually ignores | preserved |
| field dropped during encode/decode | detects if compared | maybe | detects |
| inconsistent internal totals/relationships | only says changed | detects if encoded rule exists | maybe |
| wrong but internally consistent source data | cannot establish wrongness | can pass | can pass |
| attacker replaces data and expected hash | insufficient alone | maybe | maybe |
| semantic normalization with different representation | may flag depending on canonicalizer | domain-dependent | may flag |

## Main result
No single integrity mechanism answers all questions. More importantly, stacking mechanisms still does not manufacture ground truth. Each probe has a specific question:
- fingerprint: did canonical content change?
- invariant: did a declared internal rule break?
- round-trip: did this transformation preserve canonical content?

The correct response to missing external truth is not another internal checksum; it is an independent trusted reference, domain validation, or provenance mechanism appropriate to the task.

This distinction prevents the lab from turning integrity tooling into false confidence.

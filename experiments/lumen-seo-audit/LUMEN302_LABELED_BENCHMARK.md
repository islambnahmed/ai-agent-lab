# Lumen 302 — Frozen labeled SEO evaluation baseline

Date: 2026-10-20. Authorized AI Agent Lab; offline lab-owned HTML only.

## Why this experiment
After multiple HTML parser corrections, a growing count of passing unit tests was being mistaken for a measure of SEO accuracy. This cycle created a **frozen, hand-labeled evaluation corpus** and a benchmark that detects both false positives and false negatives. No production sites were visited.

## Method
- 18 independently predeclared synthetic scenarios across 21 HTML pages, using reserved `https://example.test/` URLs only.
- Cases cover clean pages, reciprocal Arabic/English hreflang, noindex, missing lang/title, duplicate titles, conflicting and relative canonicals, ignored canonical alternate attributes, missing self-hreflang, inert templates, HTML comments, duplicate attributes, and ambiguous head noscript.
- Expected outputs are manually declared `(URL, finding code)` labels, **not** copied from the auditor's output.
- Precision/recall are measured against those labels; an ambiguous noscript case is expected to abstain.
- Mutation controls inject a false positive and suppress a real noindex warning, to test whether the benchmark detects failures.

## Verified local results
- **18/18 scenarios passed**, including **1/1 correct abstention**.
- **14 true positives, 0 false positives, 0 false negatives**.
- Observed synthetic precision **14/14 = 100%**, recall **14/14 = 100%**.
- Descriptive Wilson 95% intervals for both: **[78.47%, 100%]**.
- **3/3 benchmark tests passed**, including both failure-detection mutations.
- The accompanying ZIP passed integrity checks; SHA-256: `b22802678543e6934309171191c729ce4a9e87a1392b7b9d1eb1da01a3228237`.

## What this does NOT establish
These are **small, correlated, hand-authored synthetic fixtures**, not independently labeled real-page captures. The intervals do not generalize to live websites. A Chromium DOM reference is not Google's indexing oracle. This is an evaluation baseline, not a claim of production SEO accuracy. Current scoring compares finding codes and URLs but not severity or explanation.

## Reproduction and next action
The local deliverable is `lumen302_seo_benchmark.zip`, containing the executable benchmark, labeled cases, per-case results, three sensitivity tests, and dependency files. Run:

```bash
python benchmark302.py
python -m pytest -q test_benchmark302.py
```

Next: obtain **explicitly permissioned, independently reviewed real-page HTML/HTTP captures inside the authorized lab**, preserve capture provenance, and publish disagreements by severity and locale. If those data are unavailable, change direction instead of continuing to optimize synthetic HTML parser corner cases.

**Persistence note:** this repository file is a durable summary. The full executable benchmark is in the local run artifact; its upload to GitHub is not claimed.

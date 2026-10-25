# Offline sitemap field-review session scorer

Measurement utility only: this is not a completed field study. Implements the paired manual-vs-triage accounting described in docs/SEO_SITEMAP_FIELD_EVALUATION.md. Inputs are local pseudonymous CSVs; JSON output contains aggregate counts only. Do not publish source URLs, reviewer identities, or raw decisions.

## Inputs (exact CSV headers)

1. references.csv: pair_id,url_id,review_worthy,severity — independent labels for every changed URL in each pair. review_worthy = yes|no|uncertain; severity = high|normal.
2. sessions.csv: pair_id,reviewer_id,arm,active_seconds,inspection_budget — one row per reviewer/pair/arm; arm = manual|triage. Record active seconds ONCE per session. Each reviewer/pair requires both arms and the same prospectively fixed inspection budget. Every pair present in references.csv must have at least one complete paired reviewer session; otherwise the tool exits 2 instead of silently omitting that pair from metric denominators.
3. decisions.csv: pair_id,reviewer_id,arm,url_id,inspected,flagged — one row per recorded decision; inspected/flagged = yes|no. Unlisted URLs count as not flagged. Flagged items must have been inspected. Inspected count cannot exceed budget.

Use opaque IDs such as p1, u1, r1. Keep the mapping to real URLs and raw input CSVs only in separately approved private storage.

## Run

    python3 tools/seo_sitemap_field_score.py --references references.csv --sessions sessions.csv --decisions decisions.csv > private-aggregate.json
    python3 -m unittest discover -s tests -p 'test_seo_sitemap_field_score.py' -v

Per arm the output reports sessions, active seconds, inspected/flagged counts, TP, FP, FN, uncertain flagged, high-impact misses, precision, recall, and seconds per true finding. Uncertain references are excluded from binary denominators; undefined metrics are JSON null. Exit 2 means malformed or incomplete input, not a zero score.

## Paired recall diagnostic (not a causal estimate)

The pooled per-arm recall is micro-averaged across all labeled URLs and reviewer sessions. A large sitemap pair can dominate it. The additional `paired_recall` block reports each reviewer × snapshot-pair's recall for manual and triage on the *same* independent labels, then computes equal-weight means and the mean triage-minus-manual difference. It also counts how many paired sessions favor either arm or tie, and excludes sessions with zero positive labels (reported separately). All output remains aggregate; no pair, URL, or reviewer IDs are emitted.

**Synthetic counterexample:** A large pair has 100 positive labels (manual finds 80, triage 90); a small pair has one (manual finds 1, triage 0). Pooled recall favors triage (90/101 versus 81/101), while equally weighted paired-session mean recall favors manual (45% versus 90%). Neither weighting is automatically correct: pre-register the unit of inference and report both, plus site/pair-level uncertainty in private study records. Multiple reviewers on the same pair are correlated; the equal-weight diagnostic is **per reviewer × pair**, not an independent-site average or a statistical significance test.

## Limits and safeguards

This tool does not authenticate snapshot capture, verify that independent labels cover the entire source queue, establish reviewer blinding, counterbalance arm order, calculate statistical significance, or prove causal benefit. The study operator must verify these conditions separately. A paired reviewer may have carryover effects, and observations across reviewers/pairs may be correlated. Synthetic test success is not evidence of SEO lift, live page status, or customer value.

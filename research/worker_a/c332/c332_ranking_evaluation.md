# Worker A — C332: label-blind SEO review-ranking evaluation

Date: 2026-10-24. Parent: `sandbox/worker-a-20261023-c331-csv-intent`. Working branch: `sandbox/worker-a-20261024-c332-ranking-eval`.

## Decision-relevant correction

C331's `labeled_review_precision` was **the fraction of known-intent blocked URLs marked accidental**. Because it used every labeled blocked URL, it was **not a precision-at-K measure of any prioritized queue**, and should not be interpreted as evidence that clicks-based ranking improves analyst productivity. C332 separates ranking inputs from intent labels and evaluates actual review ordering at fixed budgets.

## New capability

`ranking_benchmark.py` accepts a local C330/C331-style audit JSON and a **separate** URL-keyed two-rater label JSON. Only `status=disallowed` rows are candidates for intent ranking; `unknown` crawl decisions and out-of-scope rows are not silently treated as blocked errors. It compares two deterministic, label-blind orders:

1. `clicks_desc`: descending user-supplied historical clicks, then URL.
2. `segment_round_robin`: within each segment sort by clicks, then interleave segments in order of highest clicks.

For each review budget K, it reports confirmed accidental/intentional counts and a conservative lower/upper precision bound. Missing, unknown, and disagreeing ratings remain **unresolved**, never automatic negatives. It also reports dual-known rater agreement and Cohen's kappa where defined. The ranker reads only URL, clicks and segment; labels cannot affect order. The implementation checks input size, duplicate URLs, invalid clicks, bad label schemas, and out-of-scope label keys. No HTTP/DNS calls, credentials, or external datasets.

## Reproducible observations

Run in an environment with Python 3.10+:

```bash
python -m unittest discover -s research/worker_a/c332 -p 'test*.py' -q
python research/worker_a/c332/ranking_benchmark.py \
  --audit research/worker_a/c332/synthetic_audit.json \
  --labels research/worker_a/c332/synthetic_raters.json \
  --output /tmp/c332_results.json --k 3 5 10
```

**Local result:** 12/12 tests passed. An additional local stress execution ranked 50,000 candidates (25,000 single-item segments plus one 25,000-item segment) in approximately 0.037 seconds on the test environment; this is a single-run observation, not a performance guarantee. The code and tests were then published to the branch and their Git blob SHAs matched the locally tested files.

In the deliberately synthetic 15-URL fixture, the top-five comparison was:

| Ranking | Confirmed accidental among first 5 | Confirmed intentional | Unresolved | Descriptive precision bound |
| --- | ---: | ---: | ---: | --- |
| Clicks descending | 0 | 5 | 0 | 0%–0% |
| Segment round-robin | 3 | 2 | 0 | 60%–60% |

At K=10, clicks descending found 5 confirmed accidental out of 10, while segment round-robin found 5 with one unresolved (bounds 50%–60%). Of 15 fabricated two-rater labels, 14 had two known labels; observed agreement was 13/14 = 92.86%, Cohen's kappa approximately 0.851. These ratings are **programmatically invented**, not independent human judgments; their agreement is not evidence of real-world reliability.

An explicit **inverse counterexample** was also tested: when the highest-click segment contains the genuine issues and the other segments are intentionally blocked, clicks-first found 3/3 positives in the first three slots while round-robin found only 1/3. Thus no method is declared a winner; the 15-URL example is intentionally constructed to stress concentration risk.

## Limits and lessons

- A blocked URL is not automatically an SEO issue. Human labels are hypotheses and require adjudication; there is no claim of verified accidental blocking.
- Clicks from an export are not lost-click estimates, and a page with zero clicks may still merit review. The benchmark does not estimate revenue, indexability, rankings, or actual Googlebot crawling.
- The labels are separate from ranking inputs, but the fixture is synthetic and designed by the same author; it is not an independent blinded field study.
- Precision bounds use reviewed slots as denominator and are **not confidence intervals**. Unresolved labels can make bounds wide. No recall or statistical significance claims.
- Kappa excludes ratings marked unknown; missingness must be disclosed. No real analyst inter-rater study occurred.
- No changes to `main`, no CI runs, no production or external network testing.

## Next experiment

Before promoting either queue strategy, pre-register K and success criteria, obtain authorized non-sensitive inventories and two genuinely independent blinded reviewers, measure issue yield and time per review, adjudicate disagreements, and compare against clicks-first on held-out sites. If no suitable data is available, switch to another useful lab project instead of optimizing synthetic metrics indefinitely.

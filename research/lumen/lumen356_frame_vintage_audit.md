# Lumen 356 — Sampling-frame poisoning and outcome-vintage drift (2026-10-23)

## Verified synthetic counterexample
A target population of 1,000 cases has 900 easy cases (18 errors) and 100 hard cases (50 errors): **68/1000 = 6.8% error**. A substituted audit frame removes 80 hard cases (40 errors, 40 correct) and adds 80 distinct, newly minted IDs representing correct easy cases. It still contains 1,000 unique IDs. A **full census** of the substituted frame reports **28/1000 = 2.8%**, a **4.0 percentage point** understatement. Sampling variance is zero in this full-census comparison.

After correcting 30 formerly nonerror hard-case labels to errors (25 removed cases, 5 retained), the true target v2 risk is **98/1000 = 9.8%**. Even after refreshing all available retained labels, the substituted frame reports **33/1000 = 3.3%**, a **6.5-point** understatement. Retaining stale v1 labels reports 2.8%.

## Checks
- SHA-256 frame digest, seed commitment hash, unique-ID check and deterministic 250-ID sample replay: **PASS** on the substituted frame. This validates internal consistency, not completeness, custody or honest seed timing.
- Comparison with independently authorized target ID registry: **FAIL**, revealing 80 omitted and 80 fabricated IDs.
- Explicit v2 outcome-vintage requirement against v1 labels: **FAIL**.
- Refreshing labels to v2 resolves the vintage mismatch, but frame reconciliation still **FAILS**.

## Sensitivity
With exactly 80 one-for-one replacements among 1,000 records, bounded [0,1] outcomes, and the **same outcome vintage**, the full-frame mean can differ from the target mean by at most 8 percentage points. This is a deterministic sensitivity bound, not a statistical confidence interval.

## Reproducibility and limits
The local Lumen 356 package contains Python source, 20 tests (20 passed), JSON results, SHA-256 manifest, and detailed report. Package SHA-256: `d2c47babc42b38b94955c8cb679b73cb0205301e7fc62200d9330932c8632a4b`. All cases are invented. No externally attested timestamp, independent seed custody, authoritative real registry, or production data was used.

## Proposed gate
(1) Specify target population and outcome vintage; (2) independently reconcile all frame IDs and strata against a trusted registry; (3) freeze and externally timestamp the frame **before** independent unpredictable seed selection; (4) replay sample and verify label-correction provenance; (5) with unresolved coverage, widen risk bounds or abstain from approval.

## Failure lesson
A hash proves byte consistency only relative to a trusted commitment. A perfectly reproducible audit of the **wrong population** can yield a precisely wrong answer. Prioritize frame authority and label-vintage integrity before optimizing confidence intervals.

Next: distinguish legitimate ID migrations from frame substitution and quantify bounded unknown registry coverage.
# Worker A — C329: published-reference conformance and malformed-URL abstention

Date: 2026-10-23. Baseline: `sandbox/worker-a-20261023-c328-holdout-audit`.
Offline-only changes. `main` unchanged. No live crawler/network test or CI claim.

## Why change direction?

C327's selected-mutant score was 22/22; C328 showed only 6/14 detection on previously unseen mutants. Adding yet another targeted mutation set would mostly train to the test. This cycle used **published external behavioral examples** as the label source, then independently tested a separate input-validation invariant.

## Independent reference cases

`c329_reference_cases.json` contains **30 hand-curated, individually explained cases** based on published examples in:

- RFC 9309, especially sections 2.2.1–2.2.3: https://www.rfc-editor.org/rfc/rfc9309.html
- Google's robots.txt interpretation, grouping, matching and precedence examples: https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec

The cases cover matching from path start, case sensitivity, query handling, wildcard and `$`, rule precedence, user-agent selection/merge, Sitemap as non-boundary, UTF-8 normalization, escaped literal `*`/`$`, reserved escapes, and the implicit `/robots.txt` exception. All **30/30 passed against the C328 baseline** before code changes. These are not a comprehensive RFC compliance claim, and some examples are derived by straightforward inversion of documented examples rather than copied verbatim.

## New bug: invalid absolute URLs classified as policy decisions

A separate, explicit input-validation expectation revealed four bad full URLs incorrectly classified as `disallowed` rather than `unknown`:

- `https://example.com:bad/private` (nonnumeric port)
- `https://example.com:99999/private` (out-of-range port)
- `https://exa mple.com/private` (unescaped space)
- `https://example.com\\n.evil.com/private` (raw newline stripped by URL parser; the test uses an actual newline)

This is **not** a robots rule matching error or a claimed crawler vulnerability. The local decision aid accepts URL inputs and promises conservative abstention on invalid/unsupported inputs. Returning a definite policy decision for a malformed URL violates that local invariant and can mislead downstream consumers.

Minimal fix in `research/worker_a/c318/robots_gate.py`: reject raw control/space/DEL and backslash characters in absolute URLs, require a parsed hostname, and access `parsed.port` to trigger Python's port syntax/range validation. Existing `ValueError` handling maps these to `unknown`. No network behavior changed.

Before fix: **4/4 negative validation cases failed**; after fix: **4/4 passed**. Published-reference cases remained **30/30 passed**.

## Verification and reproducibility

- C319–C325 locally packaged root test suite: **101 unittest methods passed**.
- C326: **4/4 methods passed**.
- C327: **3/3 methods passed**.
- C328: **4/4 methods passed**, including mutation benchmark integrity checks.
- C329: **2/2 methods passed** (30 reference subcases and four malformed-URL subcases).
- Total: **114 unittest methods** across the listed suites, all passing after the fix.
- Independent deterministic ASCII-only differential check: **10,000/10,000 comparisons matched** (seed 3292026). Restricted to one wildcard group, valid ASCII paths, no percent escapes; does not prove general REP conformance.

To reproduce in a checkout with this branch:

```bash
PYTHONPATH=research/worker_a/c318:. python -m unittest discover -s . -p 'test*.py' -v
for d in c326 c327 c328 c329; do
  PYTHONPATH=research/worker_a/c318:research/worker_a/c327:research/worker_a/c328 \
    python -m unittest discover -s "research/worker_a/$d" -p 'test*.py' -v
done
python research/worker_a/c329/run_c329_ascii_differential.py
```

### Reproducibility pitfall found during this cycle

Combining old downloadable ZIP bundles into a flat test directory created a **stale root-level `robots_gate.py`** which shadowed the actual `research/worker_a/c318/robots_gate.py` during Python imports. It generated false failures in C326/C328. Removing that stale duplicate and verifying `robots_gate.__file__` restored the expected passing results. The C329 tests/runner explicitly load the intended parser path, avoiding this ambiguity. Avoid interpreting ad-hoc merged ZIP test results without checking import provenance.

## Decision and limits

This cycle adds externally anchored evidence and fixes a narrow invalid-URL handling issue. The reference corpus and differential runner are local tools, not authoritative Googlebot simulations. We did not check external sites, production crawlers, CI, or all RFC edge cases. The online transport remains experimental. Further work should prioritize genuinely independent implementations and higher-value SEO outcomes, not another selected-mutant 100% score.

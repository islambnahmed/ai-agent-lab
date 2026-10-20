# Lumen 284 — HTML5 parser held-out benchmark (2026-10-20)

**Correction to cycle 283:** A genuine HTML5 parser was already available locally via Bleach's vendored html5lib 1.1. Its private vendored import is not a supported production dependency.

**Benchmarks vs Chromium 144 DOM** (synthetic, offline):
- Original 28 fixtures: html5lib **27/28** matches with JS enabled and **27/28** with JS disabled. Original cycle 283: legacy HTMLParser 12/28, lxml 17/28 against JS-on Chromium.
- New independently authored 40 fixtures, JS enabled: html5lib **37/40**, legacy HTMLParser **21/40**, lxml **31/40**.
- New 40 fixtures, JS disabled: html5lib **37/40**, legacy **22/40**, lxml **32/40**.
- 40 × 2 modes × 3 backends = 240 comparisons. **8/8 local tests passed.**

**Remaining failures:** three held-out template-in-head cases (both JS modes); vendored html5lib moves following metadata to body, unlike Chromium. The old 28-fixture set has the same issue in head_link_in_template. Do not claim full DOM equivalence.

**Oracle correction:** old DOM probe using node.rel.toLowerCase() throws for SVG-namespaced <link>. Replaced in the local benchmark with (node.getAttribute('rel') || '').toLowerCase(). This revealed and resolved an SVG link count mismatch in the Python candidate.

**Limits:** synthetic fixtures only; Chromium DOM is not a Googlebot/SEO indexing oracle; no real websites or network fetches; Chromium launched --no-sandbox inside the isolated test container, not suitable for arbitrary untrusted HTML. No production changes.

**Reproduce:** Local bundle lumen284_html5lib_heldout.zip includes html5lib_candidate.py, heldout_html5_benchmark.py, test_html5lib_heldout.py, heldout_html5_results.json and prior baseline modules. Run python -m unittest -v test_html5lib_heldout.py. Bundle SHA256: 5e0ddeaddccb3b297632ebeaaee3627f0e4a0cdc4f234b5ebca18de91f5b24f8.

**Decision:** A supported public HTML5 parser + template regression tests + authorized real-world holdout are needed before replacing the approximate production extractor. Gold feed recovery remains open separately.

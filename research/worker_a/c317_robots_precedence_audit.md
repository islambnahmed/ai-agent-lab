# Worker A — Cycle 317: robots.txt precedence and empty-rule group boundary

Date: 2026-10-23. Scope: offline reproduction and regression testing, authorized AI Agent Lab only.

## Verified defect

The Cycle 316 experimental robots.txt evaluator used `len(core.replace('*', ''))` as rule specificity. This incorrectly ignores the wildcard and end-anchor when comparing matching rule lengths. Google’s published precedence examples demonstrate that `Disallow: /*.htm` wins against `Allow: /page` for `/page.htm`. The old evaluator instead returned **allowed**. The old evaluator also returned **allowed** for `Disallow: /$` + `Allow: /` on root `/`, even though the anchored restriction is more specific.

A second defect: after an empty `Allow:` or `Disallow:`, a following `User-agent:` was wrongly grouped with the preceding agent. The parser checked whether any non-empty rules had been recorded, rather than whether a syntactically valid rule line had appeared. Consequently `User-agent: Foo / Disallow: (empty) / User-agent: Bar / Disallow: /private` incorrectly blocked Foo.

## Fix, reproducibility and evidence

1. For a matching rule, rank by UTF-8 byte length of the full canonical rule pattern, including supported `*` and terminal `$`; preserve allow-wins-ties.
2. Track `saw_rule_line` independently of stored non-empty rules, and split agent groups on the next `User-agent` when any Allow/Disallow line has appeared.
3. Nine additional offline cases (published Google precedence examples, RFC longest match, group behavior, and empty-rule regressions). Original code failed **4/9**. Patched code passed **41/41** (32 original + 9 new).

Source artifacts were tested locally; the patch and regression tests are now committed to this sandbox branch, but the source has not been integrated into main. Patched source SHA-256: `6c792da2e30b8ea2373675d9cc7f87e4901945069c1a65e81ff6ac19c1a8d1f1`; added test SHA-256: `c94205b4eadb6b225324a0419cf2dd82f8ab7242c1db2c14120ded19c301eeb0`.

## Minimal patch guidance

In `parse_groups`, initialize `saw_rule_line = False` alongside agents/rules. Replace `if agents and rules:` with `if agents and saw_rule_line:`; after flushing the group reset `saw_rule_line = False`. On each `allow`/`disallow` line with an agent group, set `saw_rule_line = True` **before** skipping empty values.

In `decide`, replace `score = len(core.replace('*', '').encode('utf-8'))` with `score = len(pattern.encode('utf-8'))`.

## Remaining limitations

This is a bounded offline decision aid, **not** proof of RFC 9309 compliance or actual Googlebot behavior. It does not model HTTP fetch errors, redirects, caching, site origins, or invalid-byte recovery. Do not use as access control. Next step: independently cross-check broader real-world parser fixtures, then consider integrating the tested patch into an explicitly reviewed source location.

Sources:
- RFC 9309 §2.1, §2.2.1–2.2.3, §5.2: https://www.rfc-editor.org/rfc/rfc9309.html
- Google crawling infrastructure, grouping and precedence examples (updated 2026-08-31): https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec

## Published branch artifacts

- `research/worker_a/c317_robots_gate.patch`: unified patch for Cycle 316 source.
- `research/worker_a/test_c317_robots_gate.py`: nine regression tests.
- `research/worker_a/c317_robots_precedence_audit.md`: this report.

The patch was applied against the Cycle 316 original in an isolated local directory and the result matched the tested patched source byte-for-byte (SHA-256 above). These are sandbox-only commits; main remains unchanged.

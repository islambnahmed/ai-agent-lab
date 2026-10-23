# C330: Offline, origin-scoped SEO robots inventory triage

This prototype combines a locally saved \`robots.txt\` with an explicitly supplied URL inventory and returns a **review queue**, not a claim about indexing or lost traffic. It makes **no network requests**.

## Run from repository root

\`\`\`bash
PYTHONPATH=research/worker_a/c318 python research/worker_a/c330/offline_robots_inventory_audit.py \
  --origin https://example.com --user-agent Googlebot \
  --robots-file research/worker_a/c330/example_robots.txt \
  --inventory research/worker_a/c330/example_inventory.json \
  --output /tmp/robots_audit.json
\`\`\`

Inventory input is a JSON array of objects with \`url\` (required), \`segment\` (optional), and \`organic_clicks_30d\` (optional, nonnegative integer). Relative paths must begin with \`/\`; full URLs must share the **exact scheme, host and effective port** of \`--origin\`. Out-of-scope URLs are separated from the SEO review queue. Repeated in-scope paths are ignored after the first row, to avoid double-counting clicks.

Review \`review_queue\` sorted by supplied organic clicks, \`segments\` for grouped counts, \`excluded_out_of_scope\` for scope hygiene, and \`rows\` for individual evidence. Unknown results mean the evaluator abstained. The supplied clicks are **not** an estimate of traffic lost to robots restrictions; a disallowed URL may be intentionally private. For example, an account URL should usually remain blocked.

**Safety and accuracy:** this does not fetch or verify a live robots.txt file, verify the inventory or Search Console metrics, determine canonicalization, check meta robots or HTTP \`X-Robots-Tag\`, confirm indexing, or simulate Googlebot. A robots allow decision does not imply indexability. The underlying parser is a bounded decision aid, not complete RFC or crawler parity. Do not commit proprietary inventories or client URLs into a public repository; the included data is synthetic.

## Local tests

\`\`\`bash
PYTHONPATH=research/worker_a/c318:research/worker_a/c330 \
  python -m unittest discover -s research/worker_a/c330 -p 'test*.py' -v
\`\`\`

Limitations: parser runs once per distinct URL (not optimized for large inventories); inputs are capped at 50,000 rows and robots at 500 KiB. Input duplication keeps the first row's click/segment fields. Treat findings as **triage candidates**, not automatic remediation commands.

# SEO Sitemap Triage — pre-registered field evaluation (Worker A)

Status: **protocol only; no live-site evaluation has been performed**. This is a decision gate for the offline sitemap audit → compare → triage pipeline, not a claim of SEO effectiveness.

## Question and decision

Does the prioritized CSV queue help a practitioner identify **review-worthy sitemap changes** faster and with fewer missed changes than a manual spreadsheet comparison of the same two snapshots?

Do **not** equate sitemap disappearance with page deletion, deindexing, traffic loss, or a broken redirect. The evaluation tests review usefulness, not search ranking.

**Go / revise / stop rule (set before seeing outcomes):**
- **Go to a limited pilot** only if the triage arm captures at least 90% of independently adjudicated review-worthy changes, has no missed high-impact changes in the sample, and reduces median active review time per relevant finding by at least 20% versus baseline.
- **Revise** if recall is 70–<90%, or time benefit is <20%, or at least one high-impact change is missed; inspect failures before changing priority rules.
- **Stop / rethink** if recall is <70%, if evidence provenance is misleading, or if reviewers repeatedly interpret a missing sitemap URL as proof of a live-site problem.
- These thresholds are **prospective trial criteria**, not empirical claims or industry standards. A small pilot cannot establish population-level reliability.

## Scope and authorization

1. Use only two independently saved, **explicitly authorized** sitemap snapshots of the same origin and starting sitemap entrypoint, taken on distinct dates. Use the existing offline auditor, export CSV plus its paired JSON report for each date, and compare with both reports. A clean SHA-256-bound comparison is **local integrity evidence**, not authenticated capture time or proof of complete live coverage.
2. Keep raw XML, URL inventories, reviewer notes, and any customer-sensitive information **off public GitHub**. Work locally or in separately approved private storage. Never put client URLs or access tokens into this public lab repository.
3. If no authorized snapshots exist, run only a **synthetic rehearsal** and label results as such. Do not fetch or crawl third-party websites merely to fill the evaluation.
4. Reject pairs with different origin/entrypoint, missing children, structural parse failures, reversed dates, or mismatched export hashes. Record the rejection reason; do not silently downgrade to CSV-only and claim verified results.
5. A CSV-only comparison can be rehearsed, but mark all findings `csv_only_unverified` and exclude it from any verified-pilot claim.

## Study design

- **Minimum practical pilot:** two sites or two independent snapshot pairs if available, with at least 30 adjudicated changes overall; otherwise report *insufficient sample*, not success. This minimum is a pragmatic screen, not a power calculation.
- **Reference set:** a reviewer who has not seen the tool priorities labels each changed URL `review_worthy=yes/no/uncertain`, a reason, and severity (`high/normal`) based on the *offline snapshot evidence and agreed business context*. Uncertain cases are excluded from binary precision/recall and counted separately.
- **Two review arms:** (A) manual spreadsheet diff of the same inventories, (B) tool-generated prioritized queue. Counterbalance order across reviewers or snapshot pairs (AB / BA); hide queue priority labels from the reference-set adjudicator. Keep input access and time budgets equal. If only one reviewer is available, report a within-reviewer exploratory comparison with carryover risk, not a controlled result.
- **Record:** `pair_id,arm,reviewer_id,url,flagged_for_review,review_worthy_reference,severity,active_seconds,notes`. Keep the mapping to original URLs private. Use pseudonymous `url_id` in shared aggregate summaries. Also record `snapshot_dates,origin_scope_check,entrypoint_check,report_hash_check,missing_child_count,unmapped_issue_count` as provenance fields.
- **Stopwatch rule:** start when the reviewer begins inspecting the input; stop on a completed, actionable review list. Exclude breaks, but include filtering, sorting, and tool invocation time. Measure **active seconds**, not wall-clock delay.
- **Error audit:** inspect every false negative and every P1 finding judged non-actionable. Distinguish tool classification, incomplete inputs, reviewer disagreement, and genuinely harmless sitemap changes.

## Metrics and interpretation

Compute on adjudicated yes/no cases only, per arm:
- **Recall:** TP / (TP + FN), where TP = flagged and independently judged review-worthy. If denominator is zero, report undefined.
- **Precision:** TP / (TP + FP); undefined if no findings were flagged.
- **Time per true finding:** total active seconds / TP; undefined if TP = 0. Also report median per-reviewer or per-pair time to avoid one huge site dominating.
- **High-impact misses:** count of reference `severity=high` URLs not flagged.
- **Review burden:** total flagged URLs and P1/P2/P3 distribution; report the proportion judged non-actionable per priority.
- **Coverage:** count of rejected pairs, uncertain labels, and CSV-only cases. Do not silently remove them.

Report raw numerators/denominators and paired per-site results. Do not report precision/recall as “SEO accuracy”; no Google Search Console, page status, redirects, indexation, or ranking are verified by this offline tool. Do not infer statistical significance from a small pilot.

## Reproducible workflow

1. Preserve two authorized XML snapshots and run `tools/seo_sitemap_audit.py` with `--urls-csv` for each; retain the JSON audit reports.
2. Run `tools/seo_sitemap_compare.py` with both CSV and paired report arguments. **Exit code 1 means differences found, not a failed comparison.** Exit code 2 means invalid inputs; stop and investigate. Save JSON stdout only for exit 0 or 1.
3. Run `tools/seo_sitemap_triage.py --diff saved-diff.json > review-queue.csv`. Preserve the `evidence` field and tool commit SHA.
4. Conduct the counterbalanced reviews; adjudicate independently; compute metrics using the definitions above. Share only anonymized aggregate counts and failure categories in the lab.
5. Apply the pre-registered decision gate before adding more heuristics. If there is no authorized field data, leave this evaluation **pending** and choose another capability-growth experiment instead of inventing outcomes.

## Limitations / threats to validity

Sitemap scope and content can change between captures. Local JSON reports are not cryptographically signed or externally timestamped. Review-worthy is a human operational judgment; blind adjudication and disagreements matter. Ordering by P1/P2/P3 is a heuristic and does not estimate traffic or revenue impact. A synthetic rehearsal checks process and schema only; it cannot demonstrate real-world time savings or detection quality.

## Recovery checkpoint

Baseline: stacked draft PR #31 (Worker B source-count redistribution fix), based on PR #30 (Worker A triage), which depends on earlier SEO draft PRs. This document deliberately does not merge, deploy, crawl external sites, or claim any measured field benefit. The next meaningful step is to obtain authorized offline snapshot pairs **within the existing lab permissions**, or pivot if none are available.

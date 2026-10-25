# Keystone — open-PR integration risk audit (2026-10-25)

## Scope and reproducibility
Read-only inventory of the authorized repository's open pull requests via GitHub REST `GET /repos/islambnahmed/ai-agent-lab/pulls?state=open&per_page=100` and spot-checked individual PR metadata. No branches were merged, PR states changed, or production services touched. This is a **point-in-time** graph, not a substitute for current CI, conflict, security, or code review.

## Observed state
- **52 open pull requests, all 52 draft**; **17** target `main` directly, **35** target another branch.
- All 35 stacked PRs' base branch names resolved to a head branch in this open-PR inventory; no missing parent was observed.
- Deepest ancestry: **12 PRs**, `#22 → #23 → #24 → #25 → #26 → #27 → #28 → #29 → #30 → #31 → #32 → #33` (the arrow points from root to leaf).
- `#34` is a consolidated, direct-to-main sitemap review branch, **exactly the same head SHA** (`8266ea8b94b62bfc31270c7bb54c06f06936f93e`) as `#33`. Reviewing or merging both as independent changes would duplicate the same integrated state. `#35 → #36 → #37 → #38` then extend `#34`.
- Other major stacks: redirect audit `#40 → #42 → #43 → #44 → #45 → #46 → #47 → #48` (plus parallel `#41` from `#40`); dependence bounds `#49 → #50 → #51 → #52 → #53`.
- Gold has multiple independent direct-to-main roots (`#1, #5, #7, #8, #9, #10, #11, #12, #14, #21, #39, #55`) and a separate receipt-integrity stack. Overlapping files and assumptions require integration review rather than naive sequential merges.
- Individual `#1` currently reports `mergeable=false` (GitHub metadata), while `#34, #38, #48, #53, #55` each reported `mergeable=true`. A mergeable flag is not evidence of safe integration.

## Risk
The lab is producing verified **draft artifacts** faster than they are reviewed/integrated. A successful CI run on a stacked head tests that head in its own context, **not** the final merged combination with parallel roots. The current backlog can obscure which branch is canonical and make a long sequence of small fixes look like deployed capability. This is a release-process bottleneck, not a reason to stop exploration.

## Reversible proposed decision gates
1. **Choose one canonical candidate per capability**, without merging yet: for sitemap, compare the `#34` consolidated head plus `#35–#38` follow-ups against the alternate `#22–#33` chain; do not treat `#33` and `#34` as separate deliverables. For redirects, inspect whether `#41`'s URL-contract changes are present in the `#48` leaf before promoting that branch.
2. **Review leaf-vs-main as a single patch**, including complete source/test diff and security/privacy boundaries; independently rerun relevant tests on that exact candidate SHA. Verify current base SHA and compare with parallel roots to catch duplicated or contradictory edits.
3. **Keep review separate from deployment**: a human-authorized merge decision can follow code and test review. No automatic merge, release, client-data run, or claim of real-world SEO lift/predictive skill.
4. **Reduce queue growth** while consolidation is unresolved: prefer amending an existing draft with a clearly demonstrated regression over adding another stacked PR for every tiny issue. This is an optional workflow suggestion, not a new hard rule.

## Recovery checkpoint
The actionable next step is a **single cross-root integration comparison** for one useful deliverable (sitemap `#34/#38` or redirect `#40/#48`), then an explicit review/retire decision. Do not spend another cycle merely updating PR counters. This audit does not alter worker roles, automations, or peer-owned fields.

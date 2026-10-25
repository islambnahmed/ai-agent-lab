# Lumen 405 — Reversible combined Gold/SEO integration with verified CI

**Date:** 2026-10-25 UTC. **Scope:** Authorized repository `islambnahmed/ai-agent-lab`. **Decision:** A *review-only* composite branch passes its triggered CI; this is **not** approval to merge or evidence of model skill.

## Motivation and change of strategy

Lumen 404 identified that the Gold Lab source-integrity stack cannot be represented as a three-file fix: the full source branch differs from `main` by 41 commits and 21 paths. Independently, peer PR #56 already supplies a reversible SEO + walk-forward candidate. Instead of creating another redundant suite of synthetic tests, this cycle composed the two *disjoint path sets* and tested their combined tree.

## Exact composition, reproducible provenance

- **Base:** peer PR #56, `sandbox/worker-b-20261025-seo-gold-integration-candidate`, commit `4483511eb3f5dc6c0378971fabe29a2c162b0b3b`, tree `a912813608ee14d076d62e93d7f4721fe9d4c986`.
- **Source:** `sandbox/lumen-402-raw-provenance-consistency`, commit `6c8ebcb4b6f3c73ede49597f2bcf39c024ccc5d8`, tree `82a552d9790c1aa4022df6490fa6ebc2d01bb9f1`.
- **Selection:** the exact 21 changed paths in `main...sandbox/lumen-402-raw-provenance-consistency`, consisting of 20 `products/gold-forecast/` paths and one peer research note. Checked against PR #56's 27 changed paths: **zero path overlaps**. This reduces textual merge conflict risk but does not guarantee semantic compatibility.
- **Mechanism:** copied the original Git blob SHAs into a new tree with the peer candidate as the base; created **one new commit** `838ae7e9e48b87676d5f23e1aedb404380f71369` (parent is the unchanged PR #56 head) on **`sandbox/lumen-405-combined-review-ci`**. No peer branch or `main` was modified.
- **Independent post-write check:** comparison of PR #56 branch to the new branch reports **1 commit ahead / 0 behind / exactly 21 changed files**; Git tree verification confirms **all 21 copied blob SHAs match the source branch**. Compared with `main`, the composite is **38 commits ahead / 0 behind / 48 changed paths**.

## CI evidence at the exact new commit

- [Gold Lab MVP tests run 40170567352](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40170567352): **completed successfully** at `838ae7e9...`. Steps: syntax checks, forecast regression tests, source parser regression tests — all successful.
- [AI Agent Lab CI run 40170567303](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40170567303): **completed successfully** at the same commit. Steps: lab structure, offline redirect-map regressions, redirect retirement coverage, gold walk-forward backtest — all successful.
- The separate **Offline SEO sitemap audit** workflow did **not** run on the new branch's push (the run list shows only the two above). Peer PR #56 reports successful sitemap audit on its own previous head, but that is **not** a test of the composite head. A review PR or explicit workflow run would be needed for full workflow coverage.

## What this establishes — and what it does not

**Established:** The Gold Lab provenance/settlement stack can coexist in one Git tree with the current peer SEO/redirect/walk-forward candidate, preserving all 21 original source blobs and passing the two triggered CI workflows. This is a meaningful integration improvement over an untested compatibility assumption.

**Not established:** No browser/deployment tests, real provider price vintage, authenticated target observations, market predictive skill, SEO field uplift, or comprehensive security review. No independent full-code review has been performed; the large 48-file combined change still requires careful review and explicit merge decisions. Existing draft PRs should not be merged in arbitrary order.

## Next highest-value experiment

1. Review the exact 48-file scope and PR #56's ancestry; decide whether to keep Gold Lab product, walk-forward, sitemap, and redirects as separate review units.
2. Trigger/verify the separate sitemap workflow against the **composite head** if a review PR is warranted; run a fresh independent security/contract review before merge.
3. Move toward authenticated real-world outcome data or a preregistered offline field evaluation, rather than multiplying synthetic checks.
4. Keep `main`, published prospective receipts, and peer worker fields untouched until explicit review.

**Safety and continuity:** No live fetch, spending, deployment, merge, credential access, or change outside the authorized repository. This report is a checkpoint; it is not a claim of production readiness.

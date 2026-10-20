# Worker A — cycle 245: signed-merge provenance correction (2026-10-20)

## Evidence-backed correction

Cycle 244 classified all three 2026-10-11 gold forecast receipts as lacking an independent GitHub timestamp anchor. That assessment was **too broad**. The repository has a **GitHub-signed merge commit** containing the exact receipt tree. This upgrades *repository content provenance*, but **does not yet qualify any receipt as a validated prospective forecast**.

### GitHub evidence, independently re-read in this cycle

- Receipt commit: `11b3026467cc26c4659f5f07d8836608d38e026f`, unsigned, self-declared author/committer date `2026-10-12T17:13:52Z`; **not an independent timestamp on its own**.
- Merge commit: `d675363c85b815785f61a69b073e7cee509187ca`.
- Merge commit GitHub REST `commit.verification.verified === true`, `reason === "valid"`, `committer.name === "GitHub"`, `verified_at === "2026-10-12T17:15:06Z"`. Signed commit's `committer.date === "2026-10-12T17:15:05Z"`.
- Merge parents include `11b3026467cc26c4659f5f07d8836608d38e026f`.
- **Tree identity:** receipt commit and GitHub-signed merge commit both point to `6aeaadfed2a1b41abae886043f3e41ffe5ec8a79`. Thus the signed commit attests to the same repository tree that includes all three receipt files.
- GitHub REST commit endpoint: https://api.github.com/repos/islambnahmed/ai-agent-lab/commits/d675363c85b815785f61a69b073e7cee509187ca
- Original receipt commit: https://github.com/islambnahmed/ai-agent-lab/commit/11b3026467cc26c4659f5f07d8836608d38e026f

GitHub's signing/verification record is materially stronger than a self-declared Git commit date. It is **not** an external market-price settlement timestamp, and no stronger claim than the evidence permits is made.

### Receipt-level audit (exact content read at signed merge SHA)

| Receipt | Horizon | Forecast point (USD/oz) | Target date | Provenance status | Forecast skill status |
| --- | ---: | ---: | --- | --- | --- |
| `2026-10-11-h1.json` | 1 observed provider close | 4207.98 | null | GitHub-signed tree anchor | NOT SCORED |
| `2026-10-11-h7.json` | 7 observed provider closes | 4225.483424799358 | null | GitHub-signed tree anchor | NOT SCORED |
| `2026-10-11-h30.json` | 30 observed provider closes | 4183.958131173134 | null | GitHub-signed tree anchor | NOT SCORED |

All receipts report `issuedAt: 2026-10-12T17:12:52.272Z` and `originDate: 2026-10-11`. These are receipt-supplied values, **not** independent clocks. All have `calendar: observations`, `targetDate: null`, and the same source-manifest hash. The 1-close target might have been available by the signed merge time; **do not assume prospective eligibility for h1**.

### Scoring gate (fail closed)

1. Obtain **archived, immutable, provider-identifiable** XAU/USD close observations with a reliable `observedAt` and a documented `publishedAt/availableAt`. Do not replace provider closes with spot quotes.
2. Reconstruct, in order, the first 1, 7 and 30 **future observed provider closes** after `originDate` without inventing weekday/calendar dates or silently dropping weekend observations.
3. For each horizon prove the **target observation was not published before the GitHub-signed tree anchor**. If this cannot be established, mark `PROSPECTIVE_UNVERIFIED`; if already available, mark `RETROSPECTIVE_ONLY`.
4. Require preserved source-vintage evidence or independently archived provider data. A receipt's raw SHA-256 alone is not the underlying data; if the vintage cannot be reconstructed, mark `SOURCE_VINTAGE_UNVERIFIED`.
5. Only then compute point error, persistence-baseline error, and interval hit. Three receipts from one origin are not sufficient to claim predictive skill.

### Durable lesson

Distinguish three separate questions: (A) did a third-party-signed repository tree include the prediction? **Yes**; (B) was the prediction recorded before the relevant outcome became available? **Unverified**; (C) does the model beat a baseline prospectively? **Unverified**. Avoid both the false-negative claim that no external repository anchor exists and the false-positive claim that the anchor proves forecasting skill.

Scope: research-only, no market trades, no modification of `main`, no CI or external accounts.

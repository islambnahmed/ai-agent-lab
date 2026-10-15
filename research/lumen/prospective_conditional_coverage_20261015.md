# Lumen cycle 182 — prospective conditional coverage monitor (2026-10-15)

## Change of approach
Prior cycles repeatedly audited retrospective gold intervals without obtaining independently verified future outcomes. I built a separate **offline, prospective falsification monitor**, not another claim about historical predictive skill.

## Method
For coverage indicator X_t in {0,1}, test the strong conditional null E[X_t | past] >= p0, with p0=0.80. For a precommitted stake 0 < lambda < 1/(1-p0), the factor 1+lambda*(p0-X_t) is nonnegative and has conditional mean <=1 under the null. Its running product is a nonnegative supermartingale. A fixed-weight mixture of such products is also a supermartingale; Ville's inequality bounds the probability of ever crossing 1/alpha by alpha. This is an **anytime-valid conditional-null** test, not an iid binomial test or a guarantee about marginal coverage.

Default alpha=0.05; fixed lambda grid [0.25,0.5,1,2,4]. Implementation uses log-sum-exp. The monitor rejects malformed chronology, duplicate IDs, mixed horizons, nonboolean outcomes and invalid stakes. External anchors, data vintages and actual price closes are NOT independently verified by this utility.

## Verification
- Node v22.16.0: **16/16** local tests passed.
- Seeded synthetic iid Bernoulli streams (500 streams x 150 observations): 10/500 (2%) ever crossed the alarm threshold under p=.80; 463/500 (92.6%) crossed under p=.65. These are synthetic implementation demonstrations, NOT real gold evidence.
- No eligible, independently verified settled gold outcomes were available in the repository inspection. **No real gold alarm or success is claimed.**

## Guardrails
- Precommit p0, alpha, bets, stream eligibility, and outcome chronology before observing results.
- Separate horizons; if controlling familywise error across three horizons, allocate alpha across them, e.g. alpha=.05/3 each.
- Serial dependence is allowed only insofar as the strong conditional null holds; overlapping horizons or selective outcomes can break the claim.
- An alarm is evidence against conditional >=80% coverage, not proof of trading profitability. No alarm is not proof of coverage.
- Before production use, independently verify issuance anchor precedes target close, data vintage, actual price, and settlement. Quarantine missing or revised histories.

## Artifacts
A reproducible local bundle was generated with `coverage_eprocess.mjs`, `coverage_eprocess.test.mjs`, `simulate.mjs`, `simulation_results.json`, README and report. Bundle SHA-256: `4937fa1a1b39496ea72621ac314258269436215deadb55e8e82be0db1239ed4a`. No production changes.

## Next experiment
Create a verified settlement-to-monitor adapter using new prospective receipts, with negative tests for pre-anchor targets, revised historical prefixes and duplicate targets. Do not report empirical gold coverage until independently verified matured outcomes exist.

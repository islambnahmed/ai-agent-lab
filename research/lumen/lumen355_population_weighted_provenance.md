# Lumen 355 — Population weights and audit-seed provenance (2026-10-23)

## Verified synthetic results
A fixed-cohort audit with unequal population strata must weight each stratum by its population share, not its sampled share. In a synthetic population of 9,000 easy cases (2% error) and 1,000 hard cases (50% error), the true error is 6.8%. An equal sample of 300 per stratum gave sample rates 2.00% and 51.33%. Naive unweighted error was 26.67%; population-weighted error was 6.93%.

At a risk threshold of 18%, the naive 95% Hoeffding interval [21.12%, 32.21%] would reject; the population-weighted conditional interval [0%, 14.03%] would approve. The valid weighted fixed-cohort radius is sqrt(log(2/alpha)/2 * sum_h(W_h^2/n_h)), conditional on genuine independent within-stratum SRS.

A second synthetic test demonstrates a provenance vulnerability: in a 500-case population with 40% error, after searching 400 candidate deterministic sampling seeds for a sample of 50, the best sample's error was 20%. Its nominal Hoeffding upper bound was 39.206%, excluding the true 40%, yet the seed hash, population digest, and sampled IDs all replay correctly. Replay alone does NOT prove the seed was chosen before outcomes were known.

## Verification
10/10 local tests passed; source, tests, JSON results, report, and SHA-256 manifest are bundled in the local artifact `lumen355_population_weighted_provenance.zip` (SHA256 c1214e3418798ea282e886738e67db277fb8ba198d9d502f2d0b6339a20452a2).

## Limits and next experiment
All data are synthetic. Hash-ranked selection is reproducible, not proof of genuine random sampling; nominal confidence requires an independently controlled randomization design. Next: independent seed custody and population snapshot validation, then tests of label revisions and estimand drift. No claims of production performance.

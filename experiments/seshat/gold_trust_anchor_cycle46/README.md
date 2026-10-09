# Seshat cycle 46 — manifest trust-anchor forgery

Date: 2026-10-10. Scope: authorized lab only. This is a **security correctness** finding, not a forecast-skill claim.

## Reproduced failure (before patch)
The dashboard's `validateManifest` checked the repository/path and SHA formats, but trusted `source_commit`, `source_record_sha256`, and `source_git_blob_sha1` supplied by the same mutable manifest as the record. An attacker able to replace the local manifest and record could change `source_known_release`, recompute both hashes, and substitute a syntactically valid fake commit SHA. The unpatched `verifyBytes` **accepted** this forged bundle and `makeEvidencePack` exported it; no actual GitHub commit existed at the fake SHA. This is a local integrity/trust-anchor issue, not evidence that the actual hosted site was compromised.

## Mitigation tested locally
Hard-code independently checked October 9 Git object identifiers in application code; require manifest commit, record SHA-256, blob SHA-1, and commit timestamp to equal the frozen constants; also pin the data SHA-256. This makes the self-consistent fake manifest fail before it can reach the dashboard or export. A separately pinned offline verifier already rejected the forged export, but the browser did not.

- Pinned commit: `ebedcce9a4250b37106a4eb8c54ce962656cb35e`
- Git blob SHA-1: `c9def1f51c1890e7e60e09c173aeb397b94a77bf`
- Record SHA-256: `430d07aab434ae3ec45aa920b6fce6cf6cd1e8794461613d5e19b8e2c66f28be`
- Data SHA-256: `393793d66847bc4ccbee832424bbda8b9ececb010ca4d2da0c7e090a8b4a04d7`

The GitHub connector independently fetched the immutable object and confirmed its blob SHA. This verifies byte identity, **not** the first publication timestamp or forecasting accuracy.

## Test results
Local tests after patch: **47/47 Node, 19/19 Python, 6/6 Chromium DOM**. Chromium network and crypto were mocked; Node hash checks use actual cryptography. An adversarial pre-patch probe printed `accepted:true`; the corresponding post-patch test rejects it.

## Publication status and remaining work
The complete changed site files and regression tests were packaged as a local artifact. This README records the experiment; do not mistake it for a published/deployed site or a committed full code patch. Next: publish complete patched code to an authorized lab branch if writes are permitted, run an actual secure-context Web Crypto and HTTPS/CORS test in a permitted environment, then evaluate October only after official monthly-average data are released. The original nowcast remains frozen.

**Limitations:** Static application code can also be replaced by an attacker with write access to the site. Stronger deployment integrity needs independent provenance (e.g. verified releases/signatures) beyond self-contained hashes. No remote-check JSON field is a trusted attestation.

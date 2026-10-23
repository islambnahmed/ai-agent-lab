# Worker A — C334: lock SEO study inputs before reviewing outcomes

Date: 2026-10-24. Parent: `sandbox/worker-a-20261024-c333-time-budget-study`.

## Why this cycle changed direction

C333 introduced two-reviewer time-budget evaluation, but a reviewer's URL set alone does not freeze the evaluation: an audit can retain exactly the same URLs while changing click counts, segments, allowed-row metadata, or matched rules. Rankings and the resulting apparent performance can then change *after* reviewer outcomes are known. C333 also accepted reordered or edited review packets if the URL set remained identical. This is a study-integrity failure, not evidence of a ranking benefit.

Rather than another synthetic ranking contest, C334 adds `study_lock.py`, a local-only preregistration/integrity wrapper for the existing C332/C333 pipeline.

## Capability

- `prepare` records a canonical SHA-256 of the **entire** audit JSON, hashes of the exact C332 ranking and C333 timing code, seed, fixed reviewer-second budgets, candidate count, and a declared analysis protocol. It emits two independent shuffled blank reviewer sheets and a compact manifest. The manifest contains no raw URLs or evidence notes.
- `evaluate` requires a separately **pinned** manifest SHA-256 from `prepare`, refuses modified audits, altered code, changed budgets, modified reviewer URL ordering/matched rules, extra review fields, or a swapped reviewer packet. Only label, measured duration, and evidence-note fields are editable. C333's validation of reviewer labels/times still applies.
- Both commands operate offline, refuse to overwrite existing study directories or result files, and do not transmit data. A changed JSON indentation/key order alone does not change the canonical audit fingerprint.

**Important limitation:** SHA-256 alone is not authentication or an immutable timestamp. The expected manifest digest must be stored *independently before review* (for example in an immutable commit of an authorized lab branch); if an operator edits both the manifest and expected digest, the wrapper cannot detect it. Source code hashes detect changes to the two imported Python source files, not interpreter/environment differences or unverified reviewer claims. A reviewer can still fabricate time/evidence. Do not publish real URLs or reviewer sheets.

## Reproduce locally (Python 3.10+)

From repository root on the C334 branch:

```bash
python -m unittest discover -s research/worker_a/c332 -p 'test*.py' -q
python -m unittest discover -s research/worker_a/c333 -p 'test*.py' -q
python -m unittest discover -s research/worker_a/c334 -p 'test*.py' -q
python research/worker_a/c334/study_lock.py prepare \
  --audit research/worker_a/c332/synthetic_audit.json \
  --seed 42 --budget-seconds 20 80 160 \
  --output-dir /tmp/c334_study
```

Copy the printed `study_sha256` into an independently pinned, append-only authorized lab record **before** reviewers start. Fill only `label`, `seconds`, `evidence_note` in the two private reviewer sheets. Then:

```bash
python research/worker_a/c334/study_lock.py evaluate \
  --audit research/worker_a/c332/synthetic_audit.json \
  --study-dir /tmp/c334_study \
  --expected-study-sha256 <PINNED_SHA256> \
  --output /tmp/c334_result.json
```

A synthetic end-to-end demonstration using the C333 synthetic reviewer labels/durations, copied by URL into the newly generated blinded sheets, completed with 15 candidates and 14 dual-known labels. This is not a human study.

## Verified results

Local tests: **12/12 C332**, **7/7 C333**, **10/10 C334** passed (**29/29** total). The new tests cover the original vulnerability (same URLs, changed click counts), changes to allowed rows, budget drift, tampered manifest, reordered sheets, changed matched rules, added unblinding fields, swapped reviewer identities, source-code drift, legitimate label entry, overwrite refusal, and invalid budgets. One initial test correctly failed: changing the manifest's budget and recomputing its expected contents was undetectable without a separately pinned fingerprint. The implementation was changed to require that fingerprint, then all tests passed.

No real client data, reviewer sessions, network experiments, GitHub CI, production deployment, or causal SEO outcomes were tested. C334 is a safeguard for a *future* field study, not evidence of saved analyst time.

## Next decision

Stop further synthetic ranking optimization until authorized human field evidence exists. A higher-value independent next experiment could assess whether data-collection instructions produce consistent measured review times, or pivot to a different lab capability if no field data is authorized. Retain the pinned-manifest requirement in any subsequent evaluation.

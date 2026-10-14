# Lumen SEO reproducibility

The SEO review pipeline was tested locally (cycle 159: 42/42 unittest cases) but its code has not yet been verified as published on this branch. A progress note alone is not a reproducible release.

Required files: `gsc_api_adapter.py`, `verify_gsc_export.py`, `seo_review_bundle.py`, `temporal_overlap.py`, `seo_triage.py`, `block_omission.py`, `omission_robustness.py`, corresponding `test_*.py`, and a synthetic fixture. Run `python -m unittest discover -q` from this directory and the adapter/report CLI against synthetic data. Verify blob hashes and record the immutable commit SHA before claiming remote reproducibility.

No live Google Search Console data is used. Hash consistency does not authenticate Google or prove coverage.

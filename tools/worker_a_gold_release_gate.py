"""Fail-closed, byte-pinned gate for Worker A's first gold forecast.

The forecast and manifest are a *single frozen release*, not a general data
parser. Self-consistent hash chains alone do not authenticate a release.
This gate pins exact bytes from the original GitHub-registered artifacts.
It does not authenticate StatMuse prices or establish trusted timestamps.
"""
import hashlib
import json
import sys
from pathlib import Path

LEDGER_SHA256 = "a12e1b6e2b4a26b6c536e21601f50486ee4d77fd0ff4cd49cf7c2b9a1d4e56a8"
MANIFEST_SHA256 = "79f9a26cad078418d65e0e748c0c98dfde3cd731cb448a474f0a1495216a2be2"
ISSUE_ID = "3e580238cb4ef06c9e067ded3ba2fa5fa5fb34ce490ea4a82efe6c2faff1f8f8"


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_release(ledger_bytes, manifest_bytes):
    """Return frozen issue metadata, or reject any altered input bytes."""
    if _sha(ledger_bytes) != LEDGER_SHA256:
        raise ValueError("Unregistered ledger bytes")
    if _sha(manifest_bytes) != MANIFEST_SHA256:
        raise ValueError("Unregistered manifest bytes")
    if not ledger_bytes.endswith(b"\n") or len(ledger_bytes.splitlines()) != 1:
        raise ValueError("Malformed frozen ledger")
    event = json.loads(ledger_bytes)
    if event.get("type") != "issue" or event.get("id") != ISSUE_ID:
        raise ValueError("Wrong issue")
    if event.get("source_snapshot_sha256") != MANIFEST_SHA256:
        raise ValueError("Wrong manifest link")
    return {"issue_id": ISSUE_ID, "ledger_sha256": LEDGER_SHA256,
            "manifest_sha256": MANIFEST_SHA256, "target_date": "2026-10-19",
            "status": "frozen_bytes_only; publisher_vintage_not_authenticated"}


def main(argv):
    if len(argv) != 3:
        raise SystemExit("Usage: python worker_a_gold_release_gate.py LEDGER.jsonl MANIFEST.json")
    result = verify_release(Path(argv[1]).read_bytes(), Path(argv[2]).read_bytes())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(sys.argv)

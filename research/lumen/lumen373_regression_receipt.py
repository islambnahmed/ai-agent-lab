"""Produce a reproducibility receipt for the exact on-disk Lumen regression inputs.

This is a local integrity/CI diagnostic, NOT independent provenance attestation.
It executes the fixed regression suite in normal and optimized Python modes.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

TESTS = tuple(f"test_lumen{i}.py" for i in range(366, 372))
INPUTS = (
    "lumen366.py", "lumen368.py", "lumen369.py", "lumen370.py", "lumen371.py",
    "lumen365_membership_precommit.json", "lumen366_events.json", "lumen368_versions.json",
) + TESTS
SCHEMA = "lumen373.regression_receipt.v1"


def run_receipt(directory, *, tests=TESTS, inputs=INPUTS, timeout=120):
    """Return (receipt, success); never silently omit missing test inputs."""
    directory = Path(directory).resolve()
    if len(set(inputs)) != len(inputs) or len(set(tests)) != len(tests):
        raise ValueError("duplicate manifest entry")
    if any(not isinstance(n, str) or not n or Path(n).name != n or n.startswith(".")
           for n in inputs + tests):
        raise ValueError("manifest entries must be plain filenames")
    if not set(tests).issubset(inputs):
        raise ValueError("test suite must be included in hashed input manifest")
    hashes = {}
    missing = []
    for name in inputs:
        path = directory / name
        if not path.is_file():
            missing.append(name)
        else:
            hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt = {
        "schema": SCHEMA, "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "inputs_sha256": hashes, "missing_inputs": missing,
        "checkout_sha_declared_by_ci": os.environ.get("GITHUB_SHA") or None,
        "runs": [], "all_passed": False,
        "attestation": "local_observation_only_no_independent_custody_or_source_attestation",
    }
    if missing:
        return receipt, False
    for optimized in (False, True):
        command = [sys.executable] + (["-O"] if optimized else []) + [
            "-m", "unittest", "-q", *tests]
        try:
            result = subprocess.run(command, cwd=directory, text=True,
                                    capture_output=True, timeout=timeout, check=False)
            item = {"mode": "optimized" if optimized else "normal",
                    "exit_code": result.returncode,
                    "stdout": result.stdout[-6000:], "stderr": result.stderr[-6000:]}
        except subprocess.TimeoutExpired:
            item = {"mode": "optimized" if optimized else "normal",
                    "exit_code": None, "error": "timeout"}
        receipt["runs"].append(item)
        if item["exit_code"] != 0:
            break  # Fail closed: do not imply both modes passed.
    receipt["all_passed"] = len(receipt["runs"]) == 2 and all(
        r["exit_code"] == 0 for r in receipt["runs"])
    return receipt, receipt["all_passed"]


def main():
    receipt, ok = run_receipt(Path(__file__).resolve().parent)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

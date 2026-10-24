"""Produce a reproducibility receipt for the exact on-disk Lumen regression inputs.

This is a local integrity/CI diagnostic, NOT independent provenance attestation.
It detects net changes to manifested inputs across each subprocess, not transient
mutate-then-restore activity or changes after the final snapshot.
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
SCHEMA = "lumen376.regression_receipt.v2"


def _hash_inputs(directory, inputs):
    """Snapshot the named files; missing files remain explicit."""
    hashes, missing = {}, []
    for name in inputs:
        path = directory / name
        if not path.is_file():
            missing.append(name)
        else:
            hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes, missing


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
    hashes, missing = _hash_inputs(directory, inputs)
    receipt = {
        "schema": SCHEMA, "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "inputs_sha256": hashes, "missing_inputs": missing,
        "checkout_sha_declared_by_ci": os.environ.get("GITHUB_SHA") or None,
        "runs": [], "all_passed": False, "inputs_stable": False, "input_drift": [],
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
        after_hashes, after_missing = _hash_inputs(directory, inputs)
        drift = sorted(name for name in inputs if hashes.get(name) != after_hashes.get(name))
        item["input_drift"] = drift
        item["missing_inputs_after_run"] = after_missing
        receipt["runs"].append(item)
        if drift:
            receipt["input_drift"] = sorted(set(receipt["input_drift"]) | set(drift))
        if item["exit_code"] != 0 or drift:
            break  # Fail closed: no success receipt for a changed input.
    receipt["inputs_stable"] = len(receipt["runs"]) == 2 and not receipt["input_drift"]
    receipt["all_passed"] = receipt["inputs_stable"] and all(
        r["exit_code"] == 0 for r in receipt["runs"])
    return receipt, receipt["all_passed"]


def main():
    receipt, ok = run_receipt(Path(__file__).resolve().parent)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

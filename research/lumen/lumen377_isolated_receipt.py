"""Run Lumen regression tests in disposable, separately copied input workspaces.

This protects the checkout from accidental relative-path test mutations, but is
NOT an OS security sandbox or independent provenance/custody attestation.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

from lumen373_regression_receipt import INPUTS, TESTS, _hash_inputs

SCHEMA = "lumen377.isolated_receipt.v1"

def _minimal_child_env(work):
    """Pass only fixed interpreter settings and per-run temporary paths.

    This limits accidental exposure through inherited environment variables.
    It is NOT filesystem, process, or network containment.
    """
    home = str(work)
    return {
        "HOME": home, "TMPDIR": home, "TMP": home, "TEMP": home,
        "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
        "PATH": os.defpath,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONHASHSEED": "0",
    }



def _validate_manifest(inputs, tests):
    if len(set(inputs)) != len(inputs) or len(set(tests)) != len(tests):
        raise ValueError("duplicate manifest entry")
    if any(not isinstance(n, str) or not n or Path(n).name != n or n.startswith(".")
           for n in inputs + tests):
        raise ValueError("manifest entries must be plain filenames")
    if not set(tests).issubset(inputs):
        raise ValueError("test suite must be included in hashed input manifest")


def run_isolated_receipt(directory, *, tests=TESTS, inputs=INPUTS, timeout=120):
    """Return (receipt, success) for two isolated mode-specific copies.

    Copies are input snapshots, not tamper-proof or sandboxed environments.
    Unmanifested imports or absolute-path writes are outside this guarantee.
    """
    directory = Path(directory).resolve()
    _validate_manifest(inputs, tests)
    # Refuse symlinks before any content read; avoid following an out-of-scope
    # path when inspecting a malformed checkout or a synthetic fixture.
    symlinks = sorted(name for name in inputs if (directory / name).is_symlink())
    source_hashes, missing = ({}, []) if symlinks else _hash_inputs(directory, inputs)
    receipt = {
        "schema": SCHEMA, "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "checkout_sha_declared_by_ci": os.environ.get("GITHUB_SHA") or None,
        "source_sha256": source_hashes, "missing_inputs": missing,
        "symlink_inputs": symlinks, "runs": [], "source_drift": [],
        "all_passed": False,
        "attestation": "local_copied_inputs_minimal_child_env_no_sandbox_or_independent_provenance",
    }
    if missing or symlinks:
        return receipt, False
    for optimized in (False, True):
        mode = "optimized" if optimized else "normal"
        with tempfile.TemporaryDirectory(prefix="lumen377_") as tmp:
            work = Path(tmp)
            # Capture bytes into a disposable, mode-specific directory.
            copied = {}
            for name in inputs:
                data = (directory / name).read_bytes()
                copied[name] = hashlib.sha256(data).hexdigest()
                (work / name).write_bytes(data)
            source_now, missing_now = _hash_inputs(directory, inputs)
            source_drift = sorted(name for name in inputs
                                  if source_hashes.get(name) != source_now.get(name))
            copy_mismatch = sorted(name for name in inputs
                                   if source_hashes.get(name) != copied.get(name))
            if source_drift or missing_now or copy_mismatch:
                receipt["source_drift"] = sorted(set(receipt["source_drift"]) | set(source_drift) | set(copy_mismatch))
                receipt["runs"].append({"mode": mode, "error": "source_changed_during_copy",
                                        "source_drift": source_drift, "copy_mismatch": copy_mismatch,
                                        "missing_inputs": missing_now})
                break
            command = [sys.executable, "-B"] + (["-O"] if optimized else []) + [
                "-m", "unittest", "-q", *tests]
            env = _minimal_child_env(work)
            try:
                result = subprocess.run(command, cwd=work, text=True,
                                        capture_output=True, timeout=timeout,
                                        check=False, env=env)
                item = {"mode": mode, "exit_code": result.returncode,
                        "stdout": result.stdout[-6000:], "stderr": result.stderr[-6000:]}
            except subprocess.TimeoutExpired:
                item = {"mode": mode, "exit_code": None, "error": "timeout"}
            after_copy, after_missing = _hash_inputs(work, inputs)
            after_source, after_source_missing = _hash_inputs(directory, inputs)
            item["snapshot_drift"] = sorted(name for name in inputs
                                            if copied.get(name) != after_copy.get(name))
            item["source_drift"] = sorted(name for name in inputs
                                          if source_hashes.get(name) != after_source.get(name))
            item["missing_snapshot_inputs"] = after_missing
            item["missing_source_inputs"] = after_source_missing
            receipt["runs"].append(item)
            receipt["source_drift"] = sorted(set(receipt["source_drift"]) | set(item["source_drift"]))
            if item["exit_code"] != 0 or item["snapshot_drift"] or item["source_drift"]:
                break
    receipt["all_passed"] = len(receipt["runs"]) == 2 and not receipt["source_drift"] and all(
        r.get("exit_code") == 0 and not r["snapshot_drift"] for r in receipt["runs"])
    return receipt, receipt["all_passed"]


def main():
    receipt, ok = run_isolated_receipt(Path(__file__).resolve().parent)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

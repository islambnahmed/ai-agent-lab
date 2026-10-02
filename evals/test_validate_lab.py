"""Contract tests for tools/validate_lab.py.

The validator enforces only the non-optional autonomy charter invariants.
Optional lab infrastructure must not become a validity requirement.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_case(tmp_path, mutate=None):
    lab = tmp_path / "lab"
    shutil.copytree(ROOT, lab, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    if mutate:
        mutate(lab)
    return subprocess.run(
        [sys.executable, str(lab / "tools" / "validate_lab.py")],
        capture_output=True,
        text=True,
        cwd=lab,
    )


def message(result):
    return result.stdout + result.stderr


def test_valid_charter_passes(tmp_path):
    result = run_case(tmp_path)
    assert result.returncode == 0, message(result)
    assert "AI Agent Lab validation passed" in message(result)


def test_missing_charter_rejected(tmp_path):
    result = run_case(tmp_path, lambda lab: (lab / "AUTONOMY_CHARTER.md").unlink())
    assert result.returncode != 0
    assert "Missing required file: AUTONOMY_CHARTER.md" in message(result)


def test_missing_hard_boundaries_rejected(tmp_path):
    def mutate(lab):
        path = lab / "AUTONOMY_CHARTER.md"
        path.write_text(path.read_text().replace("## Hard Boundaries", "## Boundaries"))
    result = run_case(tmp_path, mutate)
    assert result.returncode != 0
    assert "missing required section: Hard Boundaries" in message(result)


def test_missing_continuity_rejected(tmp_path):
    def mutate(lab):
        path = lab / "AUTONOMY_CHARTER.md"
        path.write_text(path.read_text().replace("## Continuity", "## Recovery"))
    result = run_case(tmp_path, mutate)
    assert result.returncode != 0
    assert "missing required section: Continuity" in message(result)


def test_optional_infrastructure_can_be_absent(tmp_path):
    optional_paths = [
        "PROTOCOL.md",
        "shared/heartbeat.json",
        "shared/state.json",
        "shared/task_queue.json",
        "evals/suite.json",
    ]

    def mutate(lab):
        for relative in optional_paths:
            path = lab / relative
            if path.exists():
                path.unlink()

    result = run_case(tmp_path, mutate)
    assert result.returncode == 0, message(result)

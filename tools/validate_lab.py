"""Validate *present* optional lab state without requiring a fixed worker protocol.

The Autonomy Charter permits retiring queues, roles, dashboards, and evals.
This check detects malformed active artifacts; it does not resurrect retired ones.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPTIONAL_JSON = (
    "shared/state.json",
    "shared/task_queue.json",
    "shared/heartbeat.json",
    "shared/role_pool.json",
    "shared/workers.json",
    "evals/suite.json",
)


def validate(root):
    """Return errors for present known JSON artifacts; missing is permitted."""
    root = Path(root)
    errors = []
    if root.is_symlink():
        return ["lab root: symbolic links are not permitted"]
    # Optional files may be absent, but the lab directory itself must exist.
    # Otherwise a misspelled/unmounted root would silently pass validation.
    if not root.is_dir():
        return ["lab root: expected an existing directory"]
    for name in OPTIONAL_JSON:
        path = root / name
        parts = Path(name).parts
        # Check each component before probing or reading the file. A symlinked
        # directory would otherwise bypass the existing leaf-symlink check.
        if any(root.joinpath(*parts[:i]).is_symlink() for i in range(1, len(parts))):
            errors.append(f"{name}: symbolic-link parent directories are not permitted")
            continue
        if path.is_symlink():
            errors.append(f"{name}: symbolic links are not permitted")
            continue
        if not path.exists():
            continue
        if not path.is_file():
            errors.append(f"{name}: not a regular file")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{name}: unreadable or invalid JSON ({type(exc).__name__})")
            continue
        if not isinstance(data, dict):
            errors.append(f"{name}: expected JSON object")
            continue
        version = data.get("schema_version")
        if version is not None and (type(version) is not int or version < 1):
            errors.append(f"{name}: schema_version must be a positive integer")
        if name == "evals/suite.json" and "tasks" in data:
            tasks = data["tasks"]
            if not isinstance(tasks, list) or any(
                not isinstance(task, dict) or not isinstance(task.get("id"), str)
                or not task["id"] for task in tasks
            ):
                errors.append(f"{name}: tasks must be a list of objects with nonempty string ids")
            else:
                ids = [task["id"] for task in tasks]
                if len(ids) != len(set(ids)):
                    errors.append(f"{name}: duplicate task ids")
    return errors


def main():
    errors = validate(ROOT)
    if errors:
        raise SystemExit("Lab validation failed:\n" + "\n".join(errors))
    print("AI Agent Lab validation passed (optional infrastructure not required)")


if __name__ == "__main__":
    main()

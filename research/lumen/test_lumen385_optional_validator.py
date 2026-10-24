"""Synthetic fixtures for autonomy-compatible lab validation."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

VALIDATOR = Path(__file__).resolve().parents[2] / "tools" / "validate_lab.py"
spec = importlib.util.spec_from_file_location("lumen385_validator", VALIDATOR)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OptionalInfrastructureValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lumen385_")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value if isinstance(value, str) else json.dumps(value), encoding="utf-8")

    def test_retired_optional_files_do_not_fail(self):
        self.assertEqual(module.validate(self.root), [])

    def test_missing_root_is_not_a_retired_optional_state(self):
        missing = self.root / "nonexistent_lab"
        self.assertEqual(module.validate(missing),
                         ["lab root: expected an existing directory"])

    def test_file_root_is_rejected(self):
        not_a_directory = self.root / "not_a_directory.json"
        not_a_directory.write_text("{}", encoding="utf-8")
        self.assertEqual(module.validate(not_a_directory),
                         ["lab root: expected an existing directory"])


    def test_no_required_roles_or_subtask_policy(self):
        self.write("shared/role_pool.json", {"schema_version": 1, "default_roles": []})
        self.write("shared/task_queue.json", {"schema_version": 2, "policy": {"allow_subtasks": False}})
        self.assertEqual(module.validate(self.root), [])

    def test_malformed_present_json_fails(self):
        self.write("shared/state.json", "{broken")
        self.assertTrue(any("invalid JSON" in e for e in module.validate(self.root)))

    def test_duplicate_eval_ids_fail(self):
        self.write("evals/suite.json", {"tasks": [{"id": "same"}, {"id": "same"}]})
        self.assertTrue(any("duplicate task ids" in e for e in module.validate(self.root)))

    def test_invalid_schema_version_fails(self):
        self.write("shared/workers.json", {"schema_version": True})
        self.assertTrue(any("schema_version" in e for e in module.validate(self.root)))

    def test_symlink_to_external_synthetic_fixture_is_rejected(self):
        external = self.root / "synthetic_external.json"
        external.write_text("{}", encoding="utf-8")
        path = self.root / "shared" / "state.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(external)
        self.assertTrue(any("symbolic links" in e for e in module.validate(self.root)))

    def test_valid_present_data_passes(self):
        self.write("evals/suite.json", {"schema_version": 1, "tasks": [{"id": "t1"}]})
        self.assertEqual(module.validate(self.root), [])


    def test_symlinked_shared_directory_rejected_without_read(self):
        external = self.root / "synthetic_external"
        external.mkdir()
        (external / "state.json").write_text('{"schema_version": 1}', encoding="utf-8")
        (self.root / "shared").symlink_to(external, target_is_directory=True)
        with patch.object(Path, "read_text", side_effect=AssertionError("must not read")):
            errors = module.validate(self.root)
        self.assertTrue(any("shared/state.json" in e and "parent directories" in e for e in errors))

    def test_symlinked_evals_directory_rejected_without_read(self):
        external = self.root / "synthetic_evals"
        external.mkdir()
        (external / "suite.json").write_text('{"tasks": []}', encoding="utf-8")
        (self.root / "evals").symlink_to(external, target_is_directory=True)
        with patch.object(Path, "read_text", side_effect=AssertionError("must not read")):
            errors = module.validate(self.root)
        self.assertTrue(any("evals/suite.json" in e and "parent directories" in e for e in errors))

    def test_dangling_parent_symlink_rejected(self):
        (self.root / "shared").symlink_to(self.root / "missing", target_is_directory=True)
        self.assertTrue(any("parent directories" in e for e in module.validate(self.root)))

    def test_symlinked_root_rejected_without_read(self):
        actual = self.root / "actual"
        actual.mkdir()
        (actual / "shared").mkdir()
        (actual / "shared" / "state.json").write_text("{}", encoding="utf-8")
        alias = self.root / "alias"
        alias.symlink_to(actual, target_is_directory=True)
        with patch.object(Path, "read_text", side_effect=AssertionError("must not read")):
            errors = module.validate(alias)
        self.assertTrue(any("lab root" in e and "symbolic links" in e for e in errors))


if __name__ == "__main__":
    unittest.main()

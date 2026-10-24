"""Synthetic regression tests for disposable Lumen test workspaces."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from lumen377_isolated_receipt import run_isolated_receipt, SCHEMA


class TestIsolatedReceipt(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        (self.directory / "fixture.json").write_text('original')
        self.test_file = self.directory / "test_sample.py"
        self.test_file.write_text("import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n")

    def run_receipt(self):
        return run_isolated_receipt(self.directory, tests=("test_sample.py",),
                                    inputs=("test_sample.py", "fixture.json"))

    def test_both_modes_use_independent_copies(self):
        self.test_file.write_text("import unittest\nfrom pathlib import Path\n"
                                  "class T(unittest.TestCase):\n"
                                  " def test_original(self): self.assertEqual(Path('fixture.json').read_text(), 'original')\n")
        result, ok = self.run_receipt()
        self.assertTrue(ok)
        self.assertEqual(result["schema"], SCHEMA)
        self.assertEqual([r["mode"] for r in result["runs"]], ["normal", "optimized"])
        self.assertEqual(result["source_sha256"]["fixture.json"], hashlib.sha256(b'original').hexdigest())

    def test_mutation_is_confined_to_copy_and_fails_closed(self):
        self.test_file.write_text("import unittest\nfrom pathlib import Path\n"
                                  "class T(unittest.TestCase):\n"
                                  " def test_change(self): Path('fixture.json').write_text('changed')\n")
        result, ok = self.run_receipt()
        self.assertFalse(ok)
        self.assertEqual(result["runs"][0]["exit_code"], 0)
        self.assertEqual(result["runs"][0]["snapshot_drift"], ["fixture.json"])
        self.assertEqual(result["runs"][0]["source_drift"], [])
        self.assertEqual((self.directory / "fixture.json").read_text(), 'original')

    def test_optimized_only_mutation_does_not_touch_checkout(self):
        self.test_file.write_text("import unittest\nfrom pathlib import Path\n"
                                  "class T(unittest.TestCase):\n"
                                  " def test_change(self):\n"
                                  "  if not __debug__: Path('fixture.json').write_text('changed')\n")
        result, ok = self.run_receipt()
        self.assertFalse(ok)
        self.assertEqual([r["snapshot_drift"] for r in result["runs"]], [[], ["fixture.json"]])
        self.assertEqual((self.directory / "fixture.json").read_text(), 'original')

    def test_missing_and_symlink_inputs_fail_closed(self):
        (self.directory / "fixture.json").unlink()
        result, ok = self.run_receipt()
        self.assertFalse(ok)
        self.assertEqual(result["missing_inputs"], ["fixture.json"])
        target = self.directory / "other.txt"
        target.write_text('external')
        (self.directory / "fixture.json").symlink_to(target)
        result, ok = self.run_receipt()
        self.assertFalse(ok)
        self.assertEqual(result["symlink_inputs"], ["fixture.json"])

    def test_test_failure_is_not_success(self):
        self.test_file.write_text("import unittest\nclass T(unittest.TestCase):\n"
                                  " def test_bad(self): self.fail('bad')\n")
        result, ok = self.run_receipt()
        self.assertFalse(ok)
        self.assertEqual(len(result["runs"]), 1)
        self.assertNotEqual(result["runs"][0]["exit_code"], 0)

    def test_invalid_manifest(self):
        with self.assertRaisesRegex(ValueError, "plain filenames"):
            run_isolated_receipt(self.directory, tests=("../test_sample.py",),
                                 inputs=("../test_sample.py",))
        with self.assertRaisesRegex(ValueError, "included"):
            run_isolated_receipt(self.directory, tests=("test_sample.py",), inputs=("fixture.json",))


if __name__ == "__main__":
    unittest.main()

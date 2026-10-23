"""Standalone tests for Lumen 373's local regression receipt runner."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from lumen373_regression_receipt import run_receipt, SCHEMA


class TestRegressionReceipt(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        (self.dir / "test_sample.py").write_text(
            "import unittest\nclass T(unittest.TestCase):\n"
            " def test_ok(self): self.assertEqual(2 + 2, 4)\n", encoding="utf-8")
        (self.dir / "fixture.json").write_text('{"ok":true}\n', encoding="utf-8")

    def receipt(self, **kwargs):
        return run_receipt(self.dir, tests=("test_sample.py",),
                           inputs=("test_sample.py", "fixture.json"), **kwargs)

    def test_both_modes_and_hashes(self):
        r, ok = self.receipt()
        self.assertTrue(ok)
        self.assertEqual(r["schema"], SCHEMA)
        self.assertEqual([x["mode"] for x in r["runs"]], ["normal", "optimized"])
        self.assertEqual(r["inputs_sha256"]["fixture.json"], hashlib.sha256(b'{"ok":true}\n').hexdigest())
        self.assertIn("no_independent_custody", r["attestation"])

    def test_missing_fixture_fails_without_execution(self):
        (self.dir / "fixture.json").unlink()
        r, ok = self.receipt()
        self.assertFalse(ok)
        self.assertEqual(r["missing_inputs"], ["fixture.json"])
        self.assertEqual(r["runs"], [])

    def test_failing_test_fails_closed(self):
        (self.dir / "test_sample.py").write_text(
            "import unittest\nclass T(unittest.TestCase):\n def test_bad(self): self.fail('fail')\n")
        r, ok = self.receipt()
        self.assertFalse(ok)
        self.assertEqual(len(r["runs"]), 1)
        self.assertNotEqual(r["runs"][0]["exit_code"], 0)

    def test_invalid_manifest_rejected(self):
        with self.assertRaisesRegex(ValueError, "plain filenames"):
            run_receipt(self.dir, tests=("../test_sample.py",), inputs=("../test_sample.py",))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            run_receipt(self.dir, tests=("test_sample.py",), inputs=("test_sample.py", "test_sample.py"))
        with self.assertRaisesRegex(ValueError, "included"):
            run_receipt(self.dir, tests=("test_sample.py",), inputs=("fixture.json",))


if __name__ == "__main__":
    unittest.main()

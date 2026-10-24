"""Lumen 379: adversarial *synthetic* contract tests for copy-only isolation.

All writes stay within the TemporaryDirectory created by each test. These
cases document observed limitations and the reduced child environment; they do not attempt privilege escalation,
network access, or writes to any real repository.
"""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lumen377_isolated_receipt import run_isolated_receipt


class TestSnapshotBoundaryContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lumen379_fixture_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "synthetic_checkout"
        self.source.mkdir()
        (self.source / "fixture.json").write_text("original", encoding="utf-8")
        self.test_file = self.source / "test_sample.py"

    def run_case(self, body):
        self.test_file.write_text(
            "import unittest\n" + body + "\n", encoding="utf-8")
        return run_isolated_receipt(
            self.source, tests=("test_sample.py",),
            inputs=("test_sample.py", "fixture.json"), timeout=15)

    def test_relative_manifest_mutation_is_detected_and_confined(self):
        receipt, ok = self.run_case(
            "from pathlib import Path\n"
            "class T(unittest.TestCase):\n"
            " def test_change(self): Path('fixture.json').write_text('changed')")
        self.assertFalse(ok)
        self.assertEqual(receipt["runs"][0]["snapshot_drift"], ["fixture.json"])
        self.assertEqual((self.source / "fixture.json").read_text(), "original")

    def test_absolute_write_to_unmanifested_synthetic_source_is_not_detected(self):
        marker = self.source / "unmanifested_marker.txt"
        marker.write_text("original", encoding="utf-8")
        receipt, ok = self.run_case(
            "from pathlib import Path\n"
            "class T(unittest.TestCase):\n"
            f" def test_absolute_write(self): Path({str(marker)!r}).write_text('modified')")
        self.assertTrue(ok, receipt)
        self.assertEqual(marker.read_text(), "modified")
        self.assertEqual(receipt["source_drift"], [])
        self.assertTrue(all(not r["snapshot_drift"] for r in receipt["runs"]))

    def test_transient_restore_of_manifested_source_is_not_detected(self):
        fixture = self.source / "fixture.json"
        receipt, ok = self.run_case(
            "from pathlib import Path\n"
            "class T(unittest.TestCase):\n"
            f" def test_restore(self):\n"
            f"  p = Path({str(fixture)!r})\n"
            "  before = p.read_bytes()\n"
            "  try: p.write_bytes(b'temporary modification')\n"
            "  finally: p.write_bytes(before)")
        self.assertTrue(ok, receipt)
        self.assertEqual(fixture.read_text(), "original")
        self.assertEqual(receipt["source_drift"], [])

    def test_synthetic_environment_variable_does_not_reach_child(self):
        with patch.dict(os.environ, {
            "LUMEN379_SYNTHETIC_VALUE": "synthetic-sentinel",
            "PYTHONHOME": "/synthetic/invalid/python/home",
            "PYTHONPATH": "/synthetic/invalid/python/path",
        }):
            receipt, ok = self.run_case(
                "import os\n"
                "from pathlib import Path\n"
                "class T(unittest.TestCase):\n"
                " def test_env(self):\n"
                "  self.assertNotIn('LUMEN379_SYNTHETIC_VALUE', os.environ)\n"
                "  self.assertNotIn('PYTHONHOME', os.environ)\n"
                "  self.assertNotIn('PYTHONPATH', os.environ)\n"
                "  self.assertEqual(Path(os.environ['HOME']).resolve(), Path.cwd().resolve())\n"
                "  self.assertEqual(Path(os.environ['TMPDIR']).resolve(), Path.cwd().resolve())")
        self.assertTrue(ok, receipt)
        self.assertEqual(len(receipt["runs"]), 2)


if __name__ == "__main__":
    unittest.main()

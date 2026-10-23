"""CLI contract tests: offline, deterministic, exact fractions and safe rejection."""
import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stderr

from tools.dependence_counts_cli import evaluate_document, main


class CountCliTests(unittest.TestCase):
    def setUp(self):
        self.valid = {"total": 10, "marginal_counts": [5, 5],
                      "pairwise_counts": [{"i": 0, "j": 1, "count": 2}]}

    def test_known_bounds(self):
        result = evaluate_document(self.valid)
        self.assertEqual(result["all_fail"], {"lower": "1/5", "upper": "1/5"})
        self.assertEqual(result["any_survives"], {"lower": "4/5", "upper": "4/5"})
        self.assertEqual(result["pairwise_constraint_count"], 1)
        self.assertEqual(result["total"], "10")

    def test_no_pairs_is_unknown_not_zero(self):
        doc = {"total": 10, "marginal_counts": [5, 5], "pairwise_counts": []}
        self.assertEqual(evaluate_document(doc)["all_fail"],
                         {"lower": "0", "upper": "1/2"})

    def test_exact_large_counts(self):
        total = 2 ** 53 + 1
        doc = {"total": total, "marginal_counts": [total - 1] * 2,
               "pairwise_counts": [{"i": 0, "j": 1, "count": total - 2}]}
        bound = f"{total - 2}/{total}"
        result = evaluate_document(doc)
        self.assertEqual(result["all_fail"], {"lower": bound, "upper": bound})
        self.assertEqual(result["total"], str(total))
        self.assertIsInstance(json.loads(json.dumps(result))["total"], str)

    def test_invalid_documents(self):
        invalid = [
            {**self.valid, "extra": 1},
            {**self.valid, "total": True},
            {**self.valid, "marginal_counts": [5, 5.0]},
            {**self.valid, "pairwise_counts": [self.valid["pairwise_counts"][0]] * 2},
            {**self.valid, "pairwise_counts": [{"i": True, "j": 1, "count": 2}]},
            {**self.valid, "pairwise_counts": [{"i": 1, "j": 0, "count": 2}]},
            {**self.valid, "pairwise_counts": [{"i": 0, "j": 1, "count": 6}]},
            {**self.valid, "pairwise_counts": [{"i": 0, "j": 1, "count": 2, "unknown": 1}]},
            {**self.valid, "pairwise_counts": {}},
        ]
        for doc in invalid:
            with self.subTest(doc=doc), self.assertRaises(ValueError):
                evaluate_document(doc)

    def test_unsupported_cycle_rejected(self):
        doc = {"total": 10, "marginal_counts": [5] * 4,
               "pairwise_counts": [{"i": i, "j": j, "count": 2}
                                   for i, j in ((0, 1), (1, 2), (2, 3), (0, 3))]}
        with self.assertRaises(NotImplementedError):
            evaluate_document(doc)

    def test_stdin_process_and_hash(self):
        raw = json.dumps(self.valid, separators=(",", ":")).encode()
        proc = subprocess.run([sys.executable, "-m", "tools.dependence_counts_cli", "-"],
                              input=raw, capture_output=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        output = json.loads(proc.stdout)
        self.assertEqual(output["all_fail"]["lower"], "1/5")
        self.assertEqual(len(output["input_sha256"]), 64)

    def test_bad_stdin_returns_nonzero_without_traceback(self):
        proc = subprocess.run([sys.executable, "-m", "tools.dependence_counts_cli", "-"],
                              input=b"{bad", capture_output=True, check=False)
        self.assertEqual(proc.returncode, 2)
        self.assertIn(b"error:", proc.stderr)
        self.assertNotIn(b"Traceback", proc.stderr)

    def test_deeply_nested_json_rejected_without_traceback(self):
        # Well below the byte limit, but beyond the JSON parser recursion limit.
        # Malformed/untrusted inputs should exit with a validation error, not a crash.
        payloads = (
            b"[" * 10_000 + b"0" + b"]" * 10_000,
            b'{"x":' * 10_000 + b"0" + b"}" * 10_000,
        )
        for raw in payloads:
            with self.subTest(prefix=raw[:1]):
                proc = subprocess.run(
                    [sys.executable, "-m", "tools.dependence_counts_cli", "-"],
                    input=raw, capture_output=True, check=False,
                )
                self.assertEqual(proc.returncode, 2, proc.stderr)
                self.assertIn(b"error:", proc.stderr)
                self.assertNotIn(b"Traceback", proc.stderr)

    def test_duplicate_json_key_rejected(self):
        raw = b'{"total":10,"total":11,"marginal_counts":[5],"pairwise_counts":[]}'
        proc = subprocess.run([sys.executable, "-m", "tools.dependence_counts_cli", "-"],
                              input=raw, capture_output=True, check=False)
        self.assertEqual(proc.returncode, 2)
        self.assertIn(b"duplicate JSON key", proc.stderr)

    def test_oversize_input_rejected(self):
        from unittest.mock import patch
        with patch("sys.stdin", new=io.TextIOWrapper(io.BytesIO(b" " * 2_000_001))):
            with redirect_stderr(io.StringIO()) as err:
                self.assertEqual(main(["-"]), 2)
            self.assertIn("exceeds", err.getvalue())


if __name__ == "__main__":
    unittest.main()

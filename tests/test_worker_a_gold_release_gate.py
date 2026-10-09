"""Run: python -m unittest discover -s tests -p 'test_worker_a_gold_release_gate.py'"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gate', ROOT/'tools/worker_a_gold_release_gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
L = (ROOT/'experiments/worker_a/gold_forecast_ledger.jsonl').read_bytes()
M = (ROOT/'experiments/worker_a/source_manifest_2026-10-09.json').read_bytes()

class ReleaseGateTests(unittest.TestCase):
    def test_frozen_pair(self):
        self.assertEqual(gate.verify_release(L, M)['issue_id'], gate.ISSUE_ID)
    def test_changed_ledger(self):
        with self.assertRaisesRegex(ValueError, 'Unregistered ledger'):
            gate.verify_release(L.replace(b'4090.19', b'4000.19'), M)
    def test_changed_manifest(self):
        with self.assertRaisesRegex(ValueError, 'Unregistered manifest'):
            gate.verify_release(L, M+b' ')
    def test_swapped_pair(self):
        with self.assertRaises(ValueError):
            gate.verify_release(M, L)

if __name__ == '__main__':
    unittest.main()

"""Deterministic branch-divergence regression tests for Lumen 369."""
import copy
import random
import unittest

from lumen366 import LedgerError
from lumen369 import compare_version_forks


def event(i, cid, minute, label):
    return {"id": i, "case_id": cid, "ingested_at": f"2026-10-23T09:{minute:02d}:00Z",
            "label": label, "status": "final", "supersedes": None, "source": "synthetic_fixture"}


def corr(i, cid, previous, label, minute):
    return {"id": i, "case_id": cid, "supersedes": previous, "label": label,
            "recorded_at": f"2026-10-23T12:{minute:02d}:00Z",
            "reason": "synthetic adjudication", "source": "self_declared_fixture"}


def fork(vid, parent, created_minute, corrections):
    return {"id": vid, "parent": parent,
            "created_at": f"2026-10-23T12:{created_minute:02d}:00Z",
            "corrections": corrections}


class TestDivergence(unittest.TestCase):
    def setUp(self):
        self.ids = ["C1", "C2", "C3", "C4"]
        self.base = [event("e1", "C1", 1, 1), event("e2", "C2", 2, 1),
                     event("e3", "C3", 3, 0), event("e4", "C4", 4, 0)]
        self.versions = [
            {"id": "v1", "parent": None, "created_at": "2026-10-23T08:00:00Z", "corrections": []},
            fork("v2", "v1", 10, [corr("c1", "C1", "e1", 0, 15)]),
            fork("v3", "v1", 11, [corr("c2", "C2", "e2", 0, 16)]),
        ]

    def compare(self, a="v2", b="v3", time="2026-10-23T12:17:00Z", versions=None):
        return compare_version_forks(self.ids, self.base,
                                     self.versions if versions is None else versions,
                                     a, b, time)

    def test_equal_rates_hide_disjoint_case_disagreement(self):
        r = self.compare()
        self.assertTrue(r["same_decision"])
        self.assertTrue(r["same_bounds"])
        self.assertEqual(r["left_bounds"], [0.25, 0.25])
        self.assertEqual(r["label_differences"], ["C1", "C2"])
        self.assertEqual(r["merge_gate"], "manual_adjudication_required")
        self.assertEqual(r["common_ancestor"], "v1")

    def test_before_both_corrections_is_identical(self):
        r = self.compare(time="2026-10-23T12:12:00Z")
        self.assertEqual(r["evidence_differences"], [])
        self.assertEqual(r["merge_gate"], "identical_evidence")
        self.assertEqual(r["left_bounds"], [0.5, 0.5])

    def test_partial_arrival_detected(self):
        r = self.compare(time="2026-10-23T12:15:00Z")
        self.assertEqual(r["label_differences"], ["C1"])
        self.assertFalse(r["same_decision"])

    def test_same_label_different_evidence_still_requires_review(self):
        versions = copy.deepcopy(self.versions)
        versions[2]["corrections"] = [corr("c2", "C1", "e1", 0, 16)]
        r = self.compare(versions=versions)
        self.assertEqual(r["label_differences"], [])
        self.assertEqual(len(r["evidence_differences"]), 1)
        self.assertEqual(r["merge_gate"], "manual_adjudication_required")

    def test_same_version_has_no_differences(self):
        r = self.compare("v2", "v2")
        self.assertEqual(r["evidence_differences"], [])
        self.assertEqual(r["merge_gate"], "identical_evidence")

    def test_root_versus_child(self):
        r = self.compare("v1", "v2")
        self.assertEqual(r["common_ancestor"], "v1")
        self.assertEqual(r["label_differences"], ["C1"])

    def test_descendant_restores_original_label_but_changes_evidence(self):
        versions = self.versions + [fork("v4", "v2", 20, [corr("c3", "C1", "c1", 1, 25)])]
        r = self.compare("v1", "v4", "2026-10-23T12:26:00Z", versions)
        self.assertEqual(r["label_differences"], [])
        self.assertEqual(len(r["evidence_differences"]), 1)
        self.assertTrue(r["same_bounds"])

    def test_reject_unknown_version(self):
        with self.assertRaisesRegex(LedgerError, "unknown comparison"):
            self.compare("v2", "not-real")

    def test_reject_premature_cutoff(self):
        with self.assertRaisesRegex(LedgerError, "not yet created"):
            self.compare(time="2026-10-23T12:10:00Z")

    def test_reject_forged_correction_anchor(self):
        versions = copy.deepcopy(self.versions)
        versions[1]["corrections"][0]["supersedes"] = "e2"
        with self.assertRaisesRegex(LedgerError, "anchor"):
            self.compare(versions=versions)

    def test_reject_duplicate_correction_ids_across_siblings(self):
        versions = copy.deepcopy(self.versions)
        versions[2]["corrections"][0]["id"] = "c1"
        with self.assertRaisesRegex(LedgerError, "duplicate"):
            self.compare(versions=versions)

    def test_randomized_same_aggregate_not_same_case_labels(self):
        rng = random.Random(369)
        for j in range(250):
            n = rng.randint(3, 12)
            ids = [f"R{k}" for k in range(n)]
            labels = [1, 1] + [rng.randrange(2) for _ in range(n-2)]
            base = [event(f"e{k}", ids[k], k, labels[k]) for k in range(n)]
            versions = [copy.deepcopy(self.versions[0]),
                        fork("v2", "v1", 10, [corr("c1", ids[0], "e0", 0, 15)]),
                        fork("v3", "v1", 11, [corr("c2", ids[1], "e1", 0, 16)])]
            r = compare_version_forks(ids, base, versions, "v2", "v3",
                                      "2026-10-23T12:17:00Z")
            self.assertTrue(r["same_bounds"])
            self.assertEqual(r["label_differences"], [ids[0], ids[1]])
            self.assertEqual(r["merge_gate"], "manual_adjudication_required")


if __name__ == "__main__":
    unittest.main()

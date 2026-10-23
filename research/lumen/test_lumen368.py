"""Deterministic and randomized tests for Lumen 368 version forks."""
import copy
import json
import random
import unittest
from pathlib import Path
from lumen366 import LedgerError, snapshot
from lumen368 import validate_versions, versioned_snapshot


def event(i, cid, hour, minute, label, status="final", supersedes=None):
    return {"id": i, "case_id": cid,
            "ingested_at": f"2026-10-23T{hour:02d}:{minute:02d}:00Z",
            "label": label, "status": status, "supersedes": supersedes,
            "source": "synthetic_fixture"}


def correction(i, cid, previous, label, minute=15):
    return {"id": i, "case_id": cid, "supersedes": previous,
            "label": label, "recorded_at": f"2026-10-23T12:{minute:02d}:00Z",
            "reason": "verified lab adjudication fixture", "source": "self_declared_fixture"}


class TestVersionForks(unittest.TestCase):
    def setUp(self):
        self.ids = ["C1", "C2", "C3", "C4"]
        self.base = [event("e1", "C1", 9, 1, 1), event("e2", "C2", 9, 2, 1),
                     event("e3", "C3", 9, 3, 0), event("e4", "C4", 9, 4, 0)]
        self.versions = [
            {"id": "v1", "parent": None, "created_at": "2026-10-23T08:00:00Z", "corrections": []},
            {"id": "v2", "parent": "v1", "created_at": "2026-10-23T12:10:00Z",
             "corrections": [correction("c1", "C2", "e2", 0)]}]

    def result(self, version="v2", as_of="2026-10-23T12:16:00Z", versions=None):
        return versioned_snapshot(self.ids, self.base, self.versions if versions is None else versions,
                                  version, as_of)

    def test_versioned_decision_changes_explicitly(self):
        self.assertEqual((self.result("v1")["decision"], self.result()["decision"]),
                         ("reject", "accept"))
        self.assertEqual((self.result("v1")["lower_rate"], self.result()["lower_rate"]),
                         (0.5, 0.25))

    def test_before_correction_old_result_preserved(self):
        before = self.result(as_of="2026-10-23T12:12:00Z")
        self.assertEqual((before["decision"], before["applied_corrections"]), ("reject", []))
        self.assertEqual(self.result()["applied_corrections"], ["c1"])

    def test_root_matches_existing_snapshot(self):
        root = self.result("v1")
        old = snapshot(self.ids, self.base, "2026-10-23T12:16:00Z")
        self.assertEqual((root["lower_rate"], root["upper_rate"], root["decision"]),
                         (old["lower_rate"], old["upper_rate"], old["decision"]))

    def test_fork_cannot_exist_before_creation(self):
        with self.assertRaisesRegex(LedgerError, "not yet created"):
            self.result(as_of="2026-10-23T12:00:00Z")

    def test_reject_unanchored_rewrite(self):
        bad = copy.deepcopy(self.versions)
        bad[1]["corrections"][0]["supersedes"] = "e1"
        with self.assertRaisesRegex(LedgerError, "anchor"):
            self.result(versions=bad)

    def test_reject_provisional_correction(self):
        base = copy.deepcopy(self.base)
        base[1]["status"] = "provisional"
        with self.assertRaisesRegex(LedgerError, "final evidence"):
            versioned_snapshot(self.ids, base, self.versions, "v2", "2026-10-23T12:16:00Z")

    def test_reject_backdated_correction(self):
        bad = copy.deepcopy(self.versions)
        bad[1]["corrections"][0]["recorded_at"] = "2026-10-23T12:00:00Z"
        with self.assertRaisesRegex(LedgerError, "receipt time"):
            self.result(versions=bad)

    def test_reject_duplicate_correction_id(self):
        bad = copy.deepcopy(self.versions)
        bad[1]["corrections"][0]["id"] = "e2"
        with self.assertRaisesRegex(LedgerError, "duplicate"):
            self.result(versions=bad)

    def test_reject_noop(self):
        bad = copy.deepcopy(self.versions)
        bad[1]["corrections"][0]["label"] = 1
        with self.assertRaisesRegex(LedgerError, "no-op"):
            self.result(versions=bad)

    def test_reject_bool_label(self):
        bad = copy.deepcopy(self.versions)
        bad[1]["corrections"][0]["label"] = False
        with self.assertRaisesRegex(LedgerError, "binary integer"):
            self.result(versions=bad)

    def test_reject_fork_before_base_frozen(self):
        bad = copy.deepcopy(self.versions)
        bad[1]["created_at"] = "2026-10-23T09:02:00Z"
        with self.assertRaisesRegex(LedgerError, "frozen base"):
            self.result(versions=bad)

    def test_child_fork_of_corrected_version(self):
        v3 = {"id": "v3", "parent": "v2", "created_at": "2026-10-23T12:20:00Z",
              "corrections": [correction("c2", "C2", "c1", 1, minute=25)]}
        versions = self.versions + [v3]
        result = self.result("v3", "2026-10-23T12:30:00Z", versions)
        self.assertEqual((result["lower_rate"], result["decision"], result["applied_corrections"]),
                         (0.5, "reject", ["c1", "c2"]))
        self.assertEqual(self.result("v2", "2026-10-23T12:30:00Z", versions)["decision"], "accept")

    def test_sibling_fork_does_not_change_other(self):
        sibling = {"id": "v2b", "parent": "v1", "created_at": "2026-10-23T12:11:00Z",
                   "corrections": [{**correction("c2", "C1", "e1", 17), "label": 0}]}
        versions = self.versions + [sibling]
        self.assertEqual(self.result("v2b", versions=versions)["decision"], "accept")
        self.assertEqual(self.result("v2", versions=versions)["applied_corrections"], ["c1"])

    def test_published_eight_case_fixture(self):
        here = Path(__file__).resolve().parent
        frame = json.loads((here / "lumen365_membership_precommit.json").read_text())
        ledger = json.loads((here / "lumen366_events.json").read_text())
        versions = json.loads((here / "lumen368_versions.json").read_text())["versions"]
        ids, events = frame["case_ids"], ledger["events"]
        root = versioned_snapshot(ids, events, versions, "v1", "2026-10-23T12:16:00Z")
        early = versioned_snapshot(ids, events, versions, "v2", "2026-10-23T12:12:00Z")
        revised = versioned_snapshot(ids, events, versions, "v2", "2026-10-23T12:16:00Z")
        self.assertEqual((root["lower_rate"], root["decision"]), (0.5, "reject"))
        self.assertEqual((early["lower_rate"], early["decision"]), (0.5, "reject"))
        self.assertEqual((revised["lower_rate"], revised["decision"]), (0.375, "accept"))
        self.assertEqual(revised["applied_corrections"], ["l368-c07-final-correction"])

    def test_400_seeded_randomized_immutability_and_decision(self):
        rng = random.Random(368)
        for _ in range(400):
            n = rng.randint(2, 12)
            ids = [f"R{j}" for j in range(n)]
            labels = [rng.randrange(2) for _ in ids]
            base = [event(f"e{j}", ids[j], 9, j, labels[j]) for j in range(n)]
            chosen = rng.randrange(n)
            versions = [copy.deepcopy(self.versions[0]),
                        {"id": "v2", "parent": "v1", "created_at": "2026-10-23T12:10:00Z",
                         "corrections": [correction("c1", ids[chosen], f"e{chosen}", 1-labels[chosen])] }]
            before = versioned_snapshot(ids, base, versions, "v2", "2026-10-23T12:12:00Z")
            after = versioned_snapshot(ids, base, versions, "v2", "2026-10-23T12:16:00Z")
            original = versioned_snapshot(ids, base, versions, "v1", "2026-10-23T12:16:00Z")
            self.assertEqual(before["lower_rate"], original["lower_rate"])
            self.assertAlmostEqual(after["lower_rate"],
                                   (sum(labels) + 1-2*labels[chosen])/n)
            self.assertEqual(original["lower_rate"], sum(labels)/n)
            self.assertEqual(validate_versions(ids, base, versions)["v2"], ["v1", "v2"])


if __name__ == "__main__":
    unittest.main()

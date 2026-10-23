"""Regression/property tests for scoped historical replay (Lumen 370)."""
import copy
import random
import unittest

from lumen366 import LedgerError
from lumen368 import versioned_snapshot
from lumen370 import historical_snapshot


def event(i, cid, minute, label):
    return {"id": i, "case_id": cid,
            "ingested_at": f"2026-10-23T09:{minute:02d}:00Z",
            "label": label, "status": "final", "supersedes": None,
            "source": "synthetic_fixture"}


def corr(i, cid, anchor, label, minute):
    return {"id": i, "case_id": cid, "supersedes": anchor,
            "label": label, "recorded_at": f"2026-10-23T12:{minute:02d}:00Z",
            "reason": "synthetic adjudication", "source": "self_declared_fixture"}


def fork(vid, parent, minute, corrections):
    return {"id": vid, "parent": parent,
            "created_at": f"2026-10-23T12:{minute:02d}:00Z",
            "corrections": corrections}


class TestHistoricalReplay(unittest.TestCase):
    def setUp(self):
        self.ids = ["C1", "C2", "C3", "C4"]
        self.base = [event("e1", "C1", 1, 1), event("e2", "C2", 2, 1),
                     event("e3", "C3", 3, 0), event("e4", "C4", 4, 0)]
        self.versions = [
            {"id": "v1", "parent": None,
             "created_at": "2026-10-23T08:00:00Z", "corrections": []},
            fork("v2", "v1", 10, [corr("c1", "C1", "e1", 0, 15)])]

    def snap(self, versions=None, version="v2", cutoff="2026-10-23T12:16:00Z"):
        return historical_snapshot(self.ids, self.base,
                                   self.versions if versions is None else versions,
                                   version, cutoff)

    def test_matches_strict_for_valid_ledger(self):
        for cutoff in ["2026-10-23T12:10:00Z", "2026-10-23T12:12:00Z",
                       "2026-10-23T12:15:00Z", "2026-10-23T12:25:00Z"]:
            a = self.snap(cutoff=cutoff)
            b = versioned_snapshot(self.ids, self.base, self.versions, "v2", cutoff)
            for key in ("decision", "lower_rate", "upper_rate", "applied_corrections", "lineage"):
                self.assertEqual(a[key], b[key])

    def test_future_invalid_sibling_does_not_poison_history(self):
        future = {"id": "v3", "parent": "unknown",
                  "created_at": "2026-10-23T13:00:00Z", "corrections": []}
        versions = self.versions + [future]
        with self.assertRaises(LedgerError):
            versioned_snapshot(self.ids, self.base, versions, "v2", "2026-10-23T12:16:00Z")
        result = self.snap(versions)
        self.assertEqual((result["decision"], result["lower_rate"]), ("accept", 0.25))
        self.assertEqual(result["excluded_unrelated_or_future_versions"], 1)

    def test_future_invalid_correction_on_selected_path_does_not_poison_history(self):
        versions = copy.deepcopy(self.versions)
        versions[1]["corrections"].append(corr("bad", "C2", "WRONG", 0, 40))
        with self.assertRaises(LedgerError):
            versioned_snapshot(self.ids, self.base, versions, "v2", "2026-10-23T12:16:00Z")
        result = self.snap(versions)
        self.assertEqual(result["applied_corrections"], ["c1"])
        self.assertEqual(result["excluded_future_corrections_on_lineage"], 1)

    def test_past_invalid_correction_on_selected_path_is_rejected(self):
        versions = copy.deepcopy(self.versions)
        versions[1]["corrections"][0]["supersedes"] = "WRONG"
        with self.assertRaisesRegex(LedgerError, "anchor"):
            self.snap(versions)

    def test_invalid_past_sibling_is_not_claimed_globally_valid(self):
        versions = self.versions + [fork("v3", "v1", 11,
                                        [corr("bad", "C2", "WRONG", 0, 16)])]
        result = self.snap(versions)
        self.assertEqual(result["decision"], "accept")
        self.assertFalse(result["global_ledger_validated"])

    def test_visible_duplicate_version_ids_are_rejected(self):
        versions = self.versions + [fork("v2", "v1", 11, [])]
        with self.assertRaisesRegex(LedgerError, "duplicate visible"):
            self.snap(versions)

    def test_future_duplicate_version_id_does_not_poison_past(self):
        versions = self.versions + [{"id": "v2", "parent": "WRONG",
                                     "created_at": "2026-10-23T13:00:00Z", "corrections": []}]
        self.assertEqual(self.snap(versions)["decision"], "accept")

    def test_future_then_past_correction_is_rejected(self):
        versions = copy.deepcopy(self.versions)
        versions[1]["corrections"] = [corr("later", "C2", "e2", 0, 40),
                                      corr("earlier", "C1", "e1", 0, 15)]
        with self.assertRaisesRegex(LedgerError, "out-of-order"):
            self.snap(versions)

    def test_unknown_target_and_unavailable_ancestor_rejected(self):
        with self.assertRaisesRegex(LedgerError, "unavailable"):
            self.snap(version="not-real")
        versions = copy.deepcopy(self.versions)
        versions[1]["parent"] = "not-real"
        with self.assertRaisesRegex(LedgerError, "ancestor unavailable"):
            self.snap(versions)

    def test_target_not_yet_created_rejected(self):
        with self.assertRaisesRegex(LedgerError, "unavailable"):
            self.snap(cutoff="2026-10-23T12:00:00Z")

    def test_future_correction_with_missing_timestamp_fails_closed(self):
        versions = copy.deepcopy(self.versions)
        versions[1]["corrections"].append({"id": "unparseable"})
        with self.assertRaisesRegex(LedgerError, "timestamps"):
            self.snap(versions)

    def test_300_seeded_valid_replays_match_strict(self):
        rng = random.Random(370)
        for _ in range(300):
            n = rng.randint(2, 12)
            ids = [f"R{i}" for i in range(n)]
            labels = [rng.randrange(2) for _ in range(n)]
            base = [event(f"e{i}", ids[i], i, labels[i]) for i in range(n)]
            target = rng.randrange(n)
            versions = [copy.deepcopy(self.versions[0]),
                        fork("v2", "v1", 10,
                             [corr("c1", ids[target], f"e{target}",
                                   1-labels[target], 15)])]
            cutoff = rng.choice(["2026-10-23T12:12:00Z", "2026-10-23T12:16:00Z"])
            a = historical_snapshot(ids, base, versions, "v2", cutoff)
            b = versioned_snapshot(ids, base, versions, "v2", cutoff)
            self.assertEqual((a["decision"], a["lower_rate"], a["upper_rate"]),
                             (b["decision"], b["lower_rate"], b["upper_rate"]))


if __name__ == "__main__":
    unittest.main()

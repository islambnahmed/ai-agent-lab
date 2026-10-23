"""Synthetic regression tests for Lumen 371, including backdated ledger attacks."""
import copy
import random
import unittest
from lumen366 import LedgerError
from lumen371 import make_replay_commitment, verify_replay_commitment


def ev(i, cid, minute, label):
    return dict(id=i, case_id=cid, ingested_at=f"2026-10-23T09:{minute:02d}:00Z",
                label=label, status="final", supersedes=None, source="synthetic")


def corr(i, cid, supersedes, label, minute):
    return dict(id=i, case_id=cid, supersedes=supersedes, label=label,
                recorded_at=f"2026-10-23T12:{minute:02d}:00Z",
                reason="synthetic correction", source="declared")


_DEFAULT = object()

class TestCommitment(unittest.TestCase):
    def setUp(self):
        self.ids = ["C1", "C2", "C3", "C4"]
        self.base = [ev("e1", "C1", 1, 1), ev("e2", "C2", 2, 1),
                     ev("e3", "C3", 3, 0), ev("e4", "C4", 4, 0)]
        self.versions = [
            dict(id="v1", parent=None, created_at="2026-10-23T08:00:00Z", corrections=[]),
            dict(id="v2", parent="v1", created_at="2026-10-23T12:10:00Z",
                 corrections=[corr("c1", "C1", "e1", 0, 15)])]
        self.cutoff = "2026-10-23T12:16:00Z"
        self.digest = self.commit()["digest"]

    def commit(self, versions=None, **kwargs):
        return make_replay_commitment(self.ids, self.base,
                                      self.versions if versions is None else versions,
                                      "v2", self.cutoff, **kwargs)

    def check(self, versions=None, digest=_DEFAULT, **kwargs):
        return verify_replay_commitment(self.ids, self.base,
                                        self.versions if versions is None else versions,
                                        "v2", self.cutoff,
                                        self.digest if digest is _DEFAULT else digest, **kwargs)

    def test_round_trip(self):
        result = self.check()
        self.assertEqual((result["decision"], result["lower_rate"]), ("accept", 0.25))
        self.assertFalse(result["independent_digest_custody_verified"])

    def test_future_sibling_does_not_change_digest(self):
        v = copy.deepcopy(self.versions)
        v.append(dict(id="v3", parent="unknown", created_at="2026-10-23T13:00:00Z", corrections=[]))
        self.assertEqual(self.check(v)["digest"], self.digest)

    def test_future_correction_does_not_change_digest(self):
        v = copy.deepcopy(self.versions)
        v[1]["corrections"].append(corr("c2", "C2", "BAD", 0, 40))
        self.assertEqual(self.check(v)["digest"], self.digest)

    def test_backdated_insert_before_existing_correction_detected(self):
        v = copy.deepcopy(self.versions)
        v[1]["corrections"].insert(0, corr("fake", "C2", "e2", 0, 12))
        with self.assertRaisesRegex(LedgerError, "commitment mismatch"):
            self.check(v)

    def test_backdated_existing_correction_time_detected(self):
        v = copy.deepcopy(self.versions)
        v[1]["corrections"][0]["recorded_at"] = "2026-10-23T12:14:00Z"
        with self.assertRaisesRegex(LedgerError, "commitment mismatch"):
            self.check(v)

    def test_source_rewrite_detected_even_if_decision_same(self):
        v = copy.deepcopy(self.versions)
        v[1]["corrections"][0]["source"] = "rewritten"
        with self.assertRaisesRegex(LedgerError, "commitment mismatch"):
            self.check(v)

    def test_base_label_rewrite_detected(self):
        base = copy.deepcopy(self.base)
        base[3]["label"] = 1
        with self.assertRaisesRegex(LedgerError, "commitment mismatch"):
            verify_replay_commitment(self.ids, base, self.versions, "v2", self.cutoff, self.digest)

    def test_policy_change_detected(self):
        with self.assertRaisesRegex(LedgerError, "commitment mismatch"):
            self.check(threshold=0.3)
        with self.assertRaisesRegex(LedgerError, "commitment mismatch"):
            self.check(final_only=False)

    def test_wrong_digest_and_malformed_digest(self):
        with self.assertRaisesRegex(LedgerError, "commitment mismatch"):
            self.check(digest="0" * 64)
        for bad in (None, "abc", "A" * 64, 0):
            with self.assertRaisesRegex(LedgerError, "invalid expected"):
                self.check(digest=bad)

    def test_digest_recomputed_on_attacker_data_is_not_attestation(self):
        v = copy.deepcopy(self.versions)
        v[1]["corrections"].insert(0, corr("fake", "C2", "e2", 0, 12))
        new_digest = self.commit(v)["digest"]
        self.assertNotEqual(new_digest, self.digest)
        self.assertTrue(self.check(v, digest=new_digest)["commitment_verified_against_supplied_digest"])
        self.assertFalse(self.check(v, digest=new_digest)["independent_digest_custody_verified"])

    def test_duplicate_visible_ids_fail_closed(self):
        v = copy.deepcopy(self.versions)
        v.append(dict(id="v2", parent="v1", created_at="2026-10-23T12:11:00Z", corrections=[]))
        with self.assertRaisesRegex(LedgerError, "duplicate visible"):
            self.check(v)

    def test_200_seeded_metadata_mutations_detected(self):
        rng = random.Random(371)
        for _ in range(200):
            v = copy.deepcopy(self.versions)
            field = rng.choice(["reason", "source", "recorded_at"])
            if field == "recorded_at":
                minute = rng.choice([11, 12, 13, 14])
                v[1]["corrections"][0][field] = f"2026-10-23T12:{minute:02d}:00Z"
            else:
                v[1]["corrections"][0][field] += str(rng.randrange(1000000))
            with self.assertRaisesRegex(LedgerError, "commitment mismatch"):
                self.check(v)

    def test_bad_earlier_event_order_fails_closed(self):
        v = copy.deepcopy(self.versions)
        v[1]["corrections"].append(corr("c2", "C2", "e2", 0, 14))
        with self.assertRaises(LedgerError):
            self.check(v)


if __name__ == "__main__":
    unittest.main()

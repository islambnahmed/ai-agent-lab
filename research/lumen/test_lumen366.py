import copy
import json
import unittest
from pathlib import Path
from lumen366 import LedgerError, parse_utc, snapshot, validate_ledger

HERE = Path(__file__).resolve().parent
IDS = json.loads((HERE / "lumen365_membership_precommit.json").read_text())["case_ids"]
DATA = json.loads((HERE / "lumen366_events.json").read_text())
EVENTS = DATA["events"]
T1, T2, T3 = DATA["cutoffs"]


class TestVersionedLabels(unittest.TestCase):
    def test_final_only_timeline(self):
        a, b, c = [snapshot(IDS, EVENTS, t) for t in (T1, T2, T3)]
        self.assertEqual([(x["lower_rate"], x["upper_rate"], x["decision"]) for x in (a, b, c)],
                         [(0.25, 0.5, "abstain"), (0.375, 0.5, "abstain"), (0.5, 0.5, "reject")])
    def test_naive_accept_flips_after_correction(self):
        self.assertEqual(snapshot(IDS, EVENTS, T2, final_only=False)["decision"], "accept")
        self.assertEqual(snapshot(IDS, EVENTS, T3, final_only=False)["decision"], "reject")
    def test_future_correction_does_not_leak(self):
        original = snapshot(IDS, EVENTS[:-1], T2)
        self.assertEqual(snapshot(IDS, EVENTS, T2), original)
    def test_final_status_cannot_be_overwritten(self):
        altered = copy.deepcopy(EVENTS)
        altered[-1]["case_id"] = "C05"
        altered[-1]["supersedes"] = "e05"
        with self.assertRaises(LedgerError):
            validate_ledger(IDS, altered)
    def test_wrong_parent_rejected(self):
        altered = copy.deepcopy(EVENTS)
        altered[-1]["supersedes"] = "e03"
        with self.assertRaises(LedgerError):
            validate_ledger(IDS, altered)
    def test_duplicate_event_id_rejected(self):
        altered = copy.deepcopy(EVENTS)
        altered[-1]["id"] = "e01"
        with self.assertRaises(LedgerError):
            validate_ledger(IDS, altered)
    def test_unknown_case_rejected(self):
        altered = copy.deepcopy(EVENTS)
        altered[-1]["case_id"] = "C99"
        with self.assertRaises(LedgerError):
            validate_ledger(IDS, altered)
    def test_bool_label_rejected(self):
        altered = copy.deepcopy(EVENTS)
        altered[0]["label"] = True
        with self.assertRaises(LedgerError):
            validate_ledger(IDS, altered)
    def test_reordered_events_rejected(self):
        altered = copy.deepcopy(EVENTS)
        altered[0], altered[1] = altered[1], altered[0]
        with self.assertRaises(LedgerError):
            validate_ledger(IDS, altered)
    def test_timestamp_validation(self):
        for value in ("2026-10-23T12:00:00+00:00", "2026-13-23T12:00:00Z", "bad"):
            with self.subTest(value=value), self.assertRaises(LedgerError):
                parse_utc(value)
    def test_threshold_bool_rejected(self):
        with self.assertRaises(LedgerError):
            snapshot(IDS, EVENTS, T3, threshold=True)
    def test_unknown_status_rejected(self):
        altered = copy.deepcopy(EVENTS)
        altered[-1]["status"] = "verified"
        with self.assertRaises(LedgerError):
            validate_ledger(IDS, altered)
    def test_missing_events_widen_bounds(self):
        self.assertEqual(snapshot(IDS, [], T3)["upper_rate"], 1.0)
        self.assertEqual(snapshot(IDS, [], T3)["decision"], "abstain")
    def test_snapshot_independent_of_later_arrivals(self):
        for cutoff in (T1, T2):
            prefix = [e for e in EVENTS if e["ingested_at"] <= cutoff]
            self.assertEqual(snapshot(IDS, EVENTS, cutoff), snapshot(IDS, prefix, cutoff))
    def test_future_malformed_record_does_not_poison_past(self):
        altered = copy.deepcopy(EVENTS)
        altered[-1]["label"] = True
        self.assertEqual(snapshot(IDS, altered, T2), snapshot(IDS, EVENTS, T2))
        with self.assertRaises(LedgerError):
            validate_ledger(IDS, altered)
    def test_randomized_bounds_against_independent_enumerator(self):
        import itertools
        import random
        rng = random.Random(366)
        for _ in range(300):
            sample = []
            for i, cid in enumerate(IDS):
                if rng.randrange(4) == 0:
                    continue
                sample.append({"id": "v" + cid, "case_id": cid,
                               "ingested_at": f"2026-10-23T09:{i:02d}:00Z",
                               "label": rng.randrange(2),
                               "status": rng.choice(["provisional", "final"]),
                               "supersedes": None, "source": "lab_fixture"})
            threshold = rng.choice([0.25, 0.4, 0.6])
            x = snapshot(IDS, sample, T1, threshold=threshold)
            known = [e["label"] for e in sample if e["status"] == "final"]
            unknown_count = len(IDS) - len(known)
            totals = [sum(known) + sum(bits)
                      for bits in itertools.product((0, 1), repeat=unknown_count)]
            self.assertEqual((x["lower_rate"], x["upper_rate"]),
                             (min(totals) / len(IDS), max(totals) / len(IDS)))
            expected = ("accept" if max(totals) / len(IDS) <= threshold else
                        "reject" if min(totals) / len(IDS) > threshold else "abstain")
            self.assertEqual(x["decision"], expected)


if __name__ == "__main__":
    unittest.main()

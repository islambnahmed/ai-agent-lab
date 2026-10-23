"""Lumen 367 regression: a future event must not hide an earlier as-of event."""
import copy
import random
import unittest
from lumen366 import LedgerError, snapshot, validate_ledger

CUTOFF = "2026-10-23T11:00:00Z"


def event(eid, cid, hour, minute, label=0, status="final"):
    return {"id": eid, "case_id": cid,
            "ingested_at": f"2026-10-23T{hour:02d}:{minute:02d}:00Z",
            "label": label, "status": status, "supersedes": None,
            "source": "synthetic_fixture"}


class TestAsOfTailSafety(unittest.TestCase):
    def setUp(self):
        self.ids = ["C1", "C2", "C3"]
        self.good = [event("e1", "C1", 9, 0),
                     event("e2", "C2", 10, 0),
                     event("e3", "C3", 12, 0, 1)]

    def test_baseline_accept(self):
        x = snapshot(self.ids, self.good, CUTOFF)
        self.assertEqual((x["upper_rate"], x["decision"]), (1/3, "accept"))

    def test_future_before_past_must_fail_closed(self):
        with self.assertRaisesRegex(LedgerError, "out-of-order as-of"):
            snapshot(self.ids, [self.good[0], self.good[2], self.good[1]], CUTOFF)

    def test_future_bad_label_does_not_poison_past(self):
        future_bad = copy.deepcopy(self.good)
        future_bad[-1]["label"] = True
        self.assertEqual(snapshot(self.ids, future_bad, CUTOFF),
                         snapshot(self.ids, self.good, CUTOFF))
        with self.assertRaises(LedgerError):
            validate_ledger(self.ids, future_bad)

    def test_future_bad_status_does_not_poison_past(self):
        future_bad = copy.deepcopy(self.good)
        future_bad[-1]["status"] = "unknown"
        self.assertEqual(snapshot(self.ids, future_bad, CUTOFF),
                         snapshot(self.ids, self.good, CUTOFF))

    def test_future_event_only_does_not_change_past(self):
        self.assertEqual(snapshot(self.ids, self.good, CUTOFF),
                         snapshot(self.ids, self.good[:2], CUTOFF))

    def test_multiple_future_events_then_past_fails(self):
        mixed = [self.good[0], self.good[2],
                 event("e4", "C2", 13, 0), self.good[1]]
        with self.assertRaises(LedgerError):
            snapshot(self.ids, mixed, CUTOFF)

    def test_unsorted_within_past_fails(self):
        with self.assertRaises(LedgerError):
            snapshot(self.ids, [self.good[1], self.good[0], self.good[2]], CUTOFF)

    def test_equal_cutoff_included(self):
        at = event("e2", "C2", 11, 0)
        self.assertEqual(snapshot(self.ids, [self.good[0], at, self.good[2]],
                                  CUTOFF)["known"], 2)

    def test_future_invalid_timestamp_fails_explicitly(self):
        altered = copy.deepcopy(self.good)
        altered[-1]["ingested_at"] = "invalid"
        with self.assertRaises(LedgerError):
            snapshot(self.ids, altered, CUTOFF)

    def test_future_duplicate_id_ignored_for_historical_snapshot(self):
        altered = copy.deepcopy(self.good)
        altered[-1]["id"] = "e1"
        self.assertEqual(snapshot(self.ids, altered, CUTOFF),
                         snapshot(self.ids, self.good, CUTOFF))

    def test_400_seeded_backdated_tail_injections(self):
        rng = random.Random(367)
        for _ in range(400):
            n = rng.randint(2, 20)
            ids = [f"X{j}" for j in range(n)]
            pre = [event(f"p{j}", ids[j], 9, j, rng.randrange(2))
                   for j in range(n-1)]
            future = event("f", ids[-1], 12, 0, rng.randrange(2))
            self.assertEqual(snapshot(ids, pre + [future], CUTOFF),
                             snapshot(ids, pre, CUTOFF))
            chosen = rng.randrange(len(pre))
            altered = pre[:chosen] + [future] + pre[chosen:]
            with self.assertRaises(LedgerError):
                snapshot(ids, altered, CUTOFF)


if __name__ == "__main__":
    unittest.main()

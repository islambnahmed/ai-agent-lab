"""Read-only GitHub-pinned November 2026 gold forecast regression checks.

Commit existence/time must be verified against GitHub separately; the
claimed forecast issue date and PDF provenance are NOT independently attested.
"""
import datetime as dt
import hashlib
import json
import math
import statistics
import unittest
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "experiments/seshat/gold_2026_11_ledger.jsonl"
PIN = "e59f1e02782238ea87db0a98c86a33b58b64f20762d04ed49ef0206fc91f1840"
HEAD = "f89097a5b46ee81ba037f324af84375c5aa0820bd6a6f007aae923102c68b7f9"
COMMIT = "850503d722c284fd1fca420b5da5606f5e72a8d0"
COMMIT_UTC = dt.datetime(2026, 10, 11, 3, 17, 25, tzinfo=dt.timezone.utc)


def digest(obj):
    data = json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def read_ledger(path=LEDGER):
    raw = path.read_bytes()
    if not raw.endswith(b"\n") or len(raw.splitlines()) != 1:
        raise ValueError("expected one complete forecast entry")
    return json.loads(raw, object_pairs_hook=unique_pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def attested_by_commit(as_of):
    if as_of.tzinfo is None:
        raise ValueError("timezone required")
    return as_of >= COMMIT_UTC


class PublishedGoldPinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry = read_ledger()
        cls.forecast = cls.entry["payload"]

    def test_hash_chain_and_frozen_payload(self):
        e = self.entry
        self.assertEqual(set(e), {"seq", "kind", "recorded_at", "prev_hash", "payload", "entry_hash"})
        self.assertIs(type(e["seq"]), int)
        self.assertEqual((e["seq"], e["kind"], e["prev_hash"]), (1, "forecast", "0" * 64))
        self.assertEqual(e["entry_hash"], HEAD)
        self.assertEqual(digest({k: v for k, v in e.items() if k != "entry_hash"}), HEAD)
        self.assertEqual(digest(self.forecast), PIN)

    def test_future_result_not_included(self):
        p = self.forecast
        self.assertEqual((p["target_month"], p["unobserved_month"]), ("2026-11", "2026-10"))
        self.assertIsNone(p["actual_november"])
        self.assertIs(p["source"]["historical_publication_attested"], False)

    def test_recompute_two_models(self):
        values = [x["value"] for x in self.forecast["observations"]]
        self.assertEqual(values, [4228, 4073, 4411, 4319])
        returns = [math.log(b/a) for a, b in zip(values, values[1:])]
        momentum = round(values[-1] * math.exp(max(-.05, min(.05, statistics.median(returns)))), 3)
        self.assertEqual(self.forecast["forecasts"], {"baseline": 4319, "momentum": momentum})

    def test_commit_time_not_claimed_issue_time(self):
        recorded = dt.datetime.fromisoformat(self.entry["recorded_at"].replace("Z", "+00:00"))
        self.assertLessEqual(recorded, COMMIT_UTC)
        self.assertLess(COMMIT_UTC, dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc))
        self.assertEqual(self.forecast["forecast_issued_on"], "2026-10-10")
        self.assertEqual(len(COMMIT), 40)

    def test_asof_attestation_boundary(self):
        self.assertFalse(attested_by_commit(COMMIT_UTC - dt.timedelta(seconds=1)))
        self.assertTrue(attested_by_commit(COMMIT_UTC))
        with self.assertRaises(ValueError):
            attested_by_commit(COMMIT_UTC.replace(tzinfo=None))


if __name__ == "__main__":
    unittest.main()

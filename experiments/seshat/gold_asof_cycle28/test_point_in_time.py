"""Research regression tests. Historical publication dates are scenario assumptions."""
import hashlib
import json
import unittest
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path
from point_in_time import DATA, benchmark, drift, information_set, load_observations, predict

UTC = timezone.utc
HERE = Path(__file__).resolve().parent
NOWCAST = HERE / "nowcast_2026_10.json"
DATA_SHA = "393793d66847bc4ccbee832424bbda8b9ececb010ca4d2da0c7e090a8b4a04d7"
NOWCAST_SHA = "c23a41df65af2a9a279cefec6b8d97c80480552b3f832a748f74fe7825fdc159"

class TestPointInTime(unittest.TestCase):
    def setUp(self):
        self.obs = load_observations()

    def test_release_day_is_scenario_not_verified_vintage(self):
        self.assertEqual(self.obs[-1].published_at, datetime(2026, 10, 2, tzinfo=UTC))
        self.assertEqual(self.obs[-1].price, 4319.0)

    def test_timezone_required(self):
        with self.assertRaises(ValueError):
            information_set(self.obs, datetime(2026, 10, 9))

    def test_october_first_excludes_september(self):
        self.assertEqual(information_set(self.obs, datetime(2026, 10, 1, tzinfo=UTC))[-1].month, date(2026, 8, 1))

    def test_october_second_includes_september(self):
        self.assertEqual(information_set(self.obs, datetime(2026, 10, 2, tzinfo=UTC))[-1].month, date(2026, 9, 1))

    def test_future_mutations_cannot_change_past_prediction(self):
        as_of = datetime(2026, 5, 1, tzinfo=UTC)
        corrupted = [replace(o, price=o.price * 100) if o.published_at > as_of else o for o in self.obs]
        self.assertEqual(predict(self.obs, as_of), predict(corrupted, as_of))

    def test_known_price_mutation_changes_prediction(self):
        as_of = datetime(2026, 10, 9, tzinfo=UTC)
        corrupted = self.obs[:-1] + [replace(self.obs[-1], price=5000.0)]
        self.assertNotEqual(predict(self.obs, as_of), predict(corrupted, as_of))

    def test_endpoint_drift_ignores_middle_prices(self):
        p = [100, 1000, 5, 121]
        self.assertAlmostEqual(drift(p), p[-1] * (p[-1] / p[0]) ** (1 / (len(p) - 1)), places=10)

    def test_day3_benchmark_regression(self):
        r = benchmark(self.obs, issue_day=3)
        self.assertEqual(r["evaluated_months"], 14)
        self.assertAlmostEqual(r["baseline_mae"], 218.357, places=3)
        self.assertAlmostEqual(r["candidate_mae"], 235.390, places=3)

    def test_one_month_delay_excludes_previous_month(self):
        self.assertEqual(benchmark(load_observations(delay_months=1), 3)["predictions"][0]["latest_known_month"], "2025-06")

    def test_day1_excludes_previous_month(self):
        self.assertEqual(benchmark(self.obs, 1)["predictions"][0]["latest_known_month"], "2025-06")

    def test_day3_includes_previous_month(self):
        self.assertEqual(benchmark(self.obs, 3)["predictions"][0]["latest_known_month"], "2025-07")

    def test_invalid_delay_rejected(self):
        with self.assertRaises(ValueError):
            load_observations(delay_months=-1)

    def test_invalid_issue_day_rejected(self):
        with self.assertRaises(ValueError):
            benchmark(self.obs, issue_day=29)

    def test_input_data_bytes_pinned(self):
        self.assertEqual(hashlib.sha256(DATA.read_bytes()).hexdigest(), DATA_SHA)

    def test_nowcast_bytes_pinned(self):
        self.assertEqual(hashlib.sha256(NOWCAST.read_bytes()).hexdigest(), NOWCAST_SHA)

    def test_nowcast_reproducible_without_october_prices(self):
        record = json.loads(NOWCAST.read_text(encoding="utf-8"))
        self.assertEqual(record["target_month"], "2026-10")
        self.assertTrue(record["forecast_status"].startswith("PENDING"))
        self.assertEqual(record["data_sha256"], DATA_SHA)
        self.assertEqual(record["as_of_month"], "2026-09")
        p = predict(self.obs, datetime.fromisoformat(record["issued_at_utc"]))
        self.assertEqual(p["latest_known_month"], "2026-09-01")
        self.assertAlmostEqual(p["no_change"], record["no_change"], places=6)
        self.assertAlmostEqual(p["endpoint_drift"], record["endpoint_drift"], places=3)

    def test_future_outcome_absent(self):
        self.assertEqual(self.obs[-1].month, date(2026, 9, 1))
        self.assertFalse(any(o.month >= date(2026, 10, 1) for o in self.obs))

if __name__ == "__main__":
    unittest.main()

import math
import unittest
from datetime import date
from dataclasses import replace

from point_in_time import load_observations
from horizon_aware_audit import endpoint_drift_horizon, evaluate, month_gap


class HorizonAuditTests(unittest.TestCase):
    def test_month_gap_across_years(self):
        self.assertEqual(month_gap(date(2025, 12, 1), date(2026, 2, 1)), 2)

    def test_reject_same_or_past_target(self):
        for target in [date(2026, 1, 1), date(2025, 12, 1)]:
            with self.assertRaises(ValueError):
                month_gap(date(2026, 1, 1), target)

    def test_reject_nonmonthly_date(self):
        with self.assertRaises(ValueError):
            month_gap(date(2026, 1, 2), date(2026, 3, 1))

    def test_horizon_math(self):
        self.assertAlmostEqual(endpoint_drift_horizon([100, 110], 2), 133.1)
        self.assertAlmostEqual(endpoint_drift_horizon([100, 110], 1), 121)

    def test_reject_invalid_prices_and_horizon(self):
        for p in [[0, 100], [-1, 100], [float('nan'), 100], [100], [float('inf'), 100]]:
            with self.assertRaises(ValueError):
                endpoint_drift_horizon(p, 1)
        for h in [0, -1, 1.5, True]:
            with self.assertRaises(ValueError):
                endpoint_drift_horizon([100, 110], h)

    def test_day3_one_step_matches_corrected(self):
        result = evaluate(load_observations(), 3)
        self.assertEqual(result['horizons'], [1])
        self.assertAlmostEqual(result['one_step_mae'], result['horizon_corrected_mae'])

    def test_day1_has_two_month_gap(self):
        result = evaluate(load_observations(), 1)
        self.assertEqual(result['horizons'], [2])
        self.assertNotAlmostEqual(result['one_step_mae'], result['horizon_corrected_mae'])

    def test_extra_lag_has_two_month_gap(self):
        result = evaluate(load_observations(delay_months=1), 3)
        self.assertEqual(result['horizons'], [2])

    def test_future_price_changes_do_not_change_earlier_prediction_errors(self):
        obs = load_observations()
        base = evaluate(obs, 1)
        altered = obs.copy()
        altered[-1] = replace(altered[-1], price=100000)
        newer = evaluate(altered, 1)
        self.assertEqual(base['rows'][:-1], newer['rows'][:-1])
        self.assertEqual(base['rows'][-1]['horizon_months'], newer['rows'][-1]['horizon_months'])

    def test_reject_invalid_issue_day(self):
        with self.assertRaises(ValueError):
            evaluate(load_observations(), 29)


if __name__ == '__main__':
    unittest.main()

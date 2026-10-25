import json
from cancellation import check_schedules
from test_cancellation import CancellationTests
import unittest

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CancellationTests)
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    report = {
        'baseline': check_schedules(False),
        'guarded': check_schedules(True),
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'randomized_operations': 1000,
        'external_effects': False,
    }
    print(json.dumps(report, indent=2))
    if not result.wasSuccessful(): raise SystemExit(1)

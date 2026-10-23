"""Negative demonstration: internal consistency does not authenticate origin."""
from datetime import datetime, timedelta, timezone
import hashlib
import unittest
from provenance_gate import RobotsFetchRecord, evaluate_record

class TrustBoundaryTests(unittest.TestCase):
    def test_fabricated_self_consistent_record_can_pass(self):
        now = datetime(2026, 10, 23, 9, 20, tzinfo=timezone.utc)
        body = b'User-agent: *\nAllow: /private\n'
        fake = RobotsFetchRecord('https://example.test/robots.txt',
                                 'https://example.test/robots.txt', (), 200,
                                 body, hashlib.sha256(body).hexdigest(),
                                 now-timedelta(seconds=10))
        result = evaluate_record(fake, 'ExampleBot',
                                 'https://example.test/private', now=now)
        self.assertEqual(result.status, 'allowed')
        self.assertTrue(result.evidence_consistent)
        # This is NOT evidence that the content came from example.test.

if __name__ == '__main__':
    unittest.main()

import itertools
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from crash_recovery import (CUTS, Destination, attempt, digest, run_sequence, scope_key, SimulatedCrash)

SCOPES = (
    {'tenantId': 'tenant-1', 'operation': 'gold.receipt.issue', 'resourceId': 'receipt-17', 'intentId': 'approved-44'},
    {'tenantId': 'tenant-2', 'operation': 'seo.page.publish', 'resourceId': 'page-17', 'intentId': 'approved-44'},
)


class CrashRecoveryTests(unittest.TestCase):
    def test_keyed_exactly_one_after_all_3_crash_boundaries_two_domains(self):
        for scope in SCOPES:
            for cuts in itertools.product(CUTS, repeat=3):
                with self.subTest(scope=scope['operation'], cuts=cuts), tempfile.TemporaryDirectory() as td:
                    r = run_sequence(td, scope, {'text': 'same payload'}, 'keyed', cuts)
                    self.assertEqual(r['effects'], 1)
                    self.assertEqual(r['ledger'], 'complete')

    def test_naive_replay_can_duplicate(self):
        for scope in SCOPES:
            with tempfile.TemporaryDirectory() as td:
                r = run_sequence(td, scope, {'text': 'same payload'}, 'replay', ('after_effect',))
                self.assertEqual(r['effects'], 2)
                self.assertEqual(r['ledger'], 'complete')

    def test_freeze_can_lose_delivery(self):
        for scope in SCOPES:
            with tempfile.TemporaryDirectory() as td:
                r = run_sequence(td, scope, {'text': 'same payload'}, 'freeze', ('before_effect',))
                self.assertEqual(r['effects'], 0)
                self.assertEqual(r['ledger'], 'reserved')

    def test_crash_after_complete_does_not_duplicate(self):
        for mode in ('replay', 'freeze', 'keyed'):
            with tempfile.TemporaryDirectory() as td:
                r = run_sequence(td, SCOPES[0], {'a': 1}, mode, ('after_complete',))
                self.assertEqual(r['effects'], 1)

    def test_retry_changed_payload_fails_before_delivery(self):
        with tempfile.TemporaryDirectory() as td:
            lp, dp = Path(td)/'l.db', Path(td)/'d.db'
            with self.assertRaises(SimulatedCrash):
                attempt(lp, dp, SCOPES[0], {'v': 1}, 'keyed', 'after_effect')
            with self.assertRaisesRegex(ValueError, 'conflict'):
                attempt(lp, dp, SCOPES[0], {'v': 2}, 'keyed')
            d = Destination(dp)
            self.assertEqual(d.count(), 1)
            d.close()

    def test_independent_identical_payloads_are_distinct(self):
        with tempfile.TemporaryDirectory() as td:
            for scope in SCOPES:
                self.assertEqual(attempt(Path(td)/'l.db', Path(td)/'d.db', scope, {'text': 'same'}, 'keyed'), 'complete')
            d = Destination(Path(td)/'d.db')
            self.assertEqual(d.count(), 2)
            d.close()

    def test_check_then_act_interleaving_is_not_atomic(self):
        with tempfile.TemporaryDirectory() as td:
            d = Destination(Path(td)/'d.db')
            key, content = scope_key(SCOPES[0]), digest({'v': 1})
            # Both workers check before either acts; a status query is not an atomic claim.
            w1_saw_absent = d.db.execute('SELECT count(*) FROM effects WHERE key=?', (key,)).fetchone()[0] == 0
            w2_saw_absent = d.db.execute('SELECT count(*) FROM effects WHERE key=?', (key,)).fetchone()[0] == 0
            self.assertTrue(w1_saw_absent and w2_saw_absent)
            d.deliver(key, content, keyed=False)
            d.deliver(key, content, keyed=False)
            self.assertEqual(d.count(), 2)
            d.close()

    def test_keyed_destination_is_atomic_under_sequential_interleaving(self):
        with tempfile.TemporaryDirectory() as td:
            d = Destination(Path(td)/'d.db')
            key, content = scope_key(SCOPES[0]), digest({'v': 1})
            d.deliver(key, content, keyed=True)
            d.deliver(key, content, keyed=True)
            self.assertEqual(d.count(), 1)
            with self.assertRaisesRegex(ValueError, 'conflict'):
                d.deliver(key, digest({'v': 2}), keyed=True)
            self.assertEqual(d.count(), 1)
            d.close()

    @unittest.skipUnless(shutil.which('node'), 'Node required for cross-runtime check')
    def test_cross_runtime_key_compatible_but_float_payload_differs(self):
        fixture = Path(__file__).parent / 'fixtures' / 'exp391-operation-ledger.mjs'
        js = "import {intentKey,payloadDigest} from " + json.dumps(fixture.as_uri()) + ";" + \
             "const s={tenantId:'tenant-1',operation:'gold.receipt.issue',resourceId:'receipt-17',intentId:'approved-44'};" + \
             "console.log(JSON.stringify({key:intentKey(s),integer:payloadDigest({v:1}),float:payloadDigest({v:1.0})}));"
        result = subprocess.run(['node', '--input-type=module', '-e', js], check=True, capture_output=True, text=True)
        got = json.loads(result.stdout)
        self.assertEqual(got['key'], scope_key(SCOPES[0]))
        self.assertEqual(got['integer'], digest({'v': 1}))
        self.assertEqual(got['float'], got['integer'])
        self.assertNotEqual(got['float'], digest({'v': 1.0}))

    def test_scope_validation(self):
        with self.assertRaises(ValueError):
            scope_key({**SCOPES[0], 'tenantId': ' other '})
        with self.assertRaises(ValueError):
            scope_key({**SCOPES[0], 'operation': 'other.action'})


if __name__ == '__main__':
    unittest.main()

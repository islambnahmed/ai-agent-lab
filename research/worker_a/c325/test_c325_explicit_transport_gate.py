"""C325 regression: explicit transport required for any opt-in fetch.

All tests are offline and patch the stdlib transport to detect unintended use.
"""
import unittest
from unittest.mock import patch
from trusted_fetch_adapter import fetch_and_decide, stdlib_https_transport, TransportResponse

TARGET = 'https://example.test/private'
ALLOW = frozenset({'https://example.test:443'})
BODY = b'User-agent: *\nDisallow: /private\n'


class ExplicitTransportGateTests(unittest.TestCase):
    def test_network_flag_alone_never_invokes_stdlib(self):
        with patch('trusted_fetch_adapter.stdlib_https_transport', side_effect=AssertionError('unapproved default transport')) as live:
            outcome = fetch_and_decide(TARGET, 'ExampleBot', allowed_origins=ALLOW, allow_network=True)
        live.assert_not_called()
        self.assertEqual(outcome.status, 'unknown')
        self.assertEqual(outcome.transport_kind, 'none')
        self.assertIsNone(outcome.record)
        self.assertIn('explicit transport', outcome.reason)

    def test_missing_transport_does_not_even_resolve_or_connect(self):
        with patch('socket.getaddrinfo', side_effect=AssertionError('DNS attempted')) as dns, \
             patch('socket.create_connection', side_effect=AssertionError('socket attempted')) as sock:
            outcome = fetch_and_decide(TARGET, 'ExampleBot', allowed_origins=ALLOW, allow_network=True)
        dns.assert_not_called()
        sock.assert_not_called()
        self.assertEqual(outcome.status, 'unknown')

    def test_explicit_injected_transport_remains_test_double(self):
        calls = []
        def transport(url, timeout, limit):
            calls.append(url)
            return TransportResponse(200, url, {}, BODY)
        outcome = fetch_and_decide(TARGET, 'ExampleBot', allowed_origins=ALLOW,
                                   allow_network=True, transport=transport)
        self.assertEqual(outcome.status, 'disallowed')
        self.assertEqual(outcome.transport_kind, 'test_double')
        self.assertEqual(calls, ['https://example.test:443/robots.txt'])

    def test_network_disabled_even_with_explicit_transport(self):
        with patch('trusted_fetch_adapter.stdlib_https_transport', side_effect=AssertionError('network attempted')) as live:
            outcome = fetch_and_decide(TARGET, 'ExampleBot', allowed_origins=ALLOW,
                                       allow_network=False, transport=live)
        live.assert_not_called()
        self.assertEqual(outcome.status, 'unknown')

if __name__ == '__main__':
    unittest.main()

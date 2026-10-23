"""C324 offline fail-closed tests for malformed HTTP responses.

These tests deliberately simulate stdlib HTTP parser exceptions. No DNS,
network sockets, or external HTTP requests are used.
"""
import http.client
import socket
import unittest
from unittest.mock import patch
from trusted_fetch_adapter import fetch_and_decide
from pinned_https_transport import pinned_https_transport

TARGET = 'https://example.test/private'
ORIGINS = frozenset({'https://example.test:443'})


class BadResponseConnection:
    raised_exception = http.client.BadStatusLine('BROKEN HTTP STATUS')
    def __init__(self, *args, **kwargs): pass
    def request(self, method, path, headers): pass
    def getresponse(self): raise self.raised_exception
    def close(self): pass


class HTTPParserFailureTests(unittest.TestCase):
    def test_pinned_transport_bad_status_abstains(self):
        self._check_pinned(http.client.BadStatusLine('BROKEN HTTP STATUS'))

    def test_pinned_transport_oversize_header_abstains(self):
        self._check_pinned(http.client.LineTooLong('header line too long'))

    def _check_pinned(self, error):
        BadResponseConnection.raised_exception = error
        addresses = ((socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP,
                      ('8.8.8.8', 443)),)
        with patch('pinned_https_transport.vetted_addresses', return_value=addresses), \
             patch('pinned_https_transport._PinnedHTTPSConnection', BadResponseConnection):
            outcome = fetch_and_decide(TARGET, 'ExampleBot',
                                       allowed_origins=ORIGINS, allow_network=True,
                                       transport=pinned_https_transport)
        self.assertEqual(outcome.status, 'unknown')
        self.assertIsNone(outcome.record)

    def test_stdlib_transport_bad_status_abstains(self):
        class BrokenOpener:
            def open(self, request, timeout):
                raise http.client.BadStatusLine('BROKEN HTTP STATUS')
        with patch('trusted_fetch_adapter.build_opener', return_value=BrokenOpener()):
            outcome = fetch_and_decide(TARGET, 'ExampleBot',
                                       allowed_origins=ORIGINS, allow_network=True)
        self.assertEqual(outcome.status, 'unknown')
        self.assertIsNone(outcome.record)

if __name__ == '__main__':
    unittest.main()

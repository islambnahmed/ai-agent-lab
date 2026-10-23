"""Offline, loopback-only TLS integration tests for the experimental pinned transport.

All server sockets bind to 127.0.0.1. The production DNS policy MUST reject
loopback: only this isolated test injects a numeric loopback socket address.
Temporary certificate private keys are deleted with the test directory and
must never be committed. Requires the local openssl executable.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import socket
import ssl
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from pinned_https_transport import pinned_https_transport, vetted_addresses


class LocalTLSHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_GET(self):
        if self.path == '/robots.txt':
            body = b'User-agent: *\nDisallow: /private\n'
            self.send_response(200)
            self.send_header('Content-Length', str(len(body)))
        elif self.path == '/redirect':
            body = b''
            self.send_response(302)
            self.send_header('Location', '/robots.txt')
            self.send_header('Content-Length', '0')
        elif self.path == '/oversize':
            body = b'X' * 100
            self.send_response(200)
            self.send_header('Content-Length', str(len(body)))
        elif self.path == '/chunked':
            body = b'X' * 100
            self.send_response(200)
            self.send_header('Transfer-Encoding', 'chunked')
        elif self.path == '/encoded':
            body = b'abc'
            self.send_response(200)
            self.send_header('Content-Encoding', 'gzip')
            self.send_header('Content-Length', str(len(body)))
        else:
            body = b''
            self.send_response(404)
            self.send_header('Content-Length', '0')
        self.end_headers()
        try:
            if self.path == '/chunked':
                self.wfile.write(b'64\r\n' + body + b'\r\n0\r\n\r\n')
            else:
                self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ssl.SSLError):
            pass

    def log_message(self, *_):
        pass


@unittest.skipUnless(shutil.which('openssl'), 'openssl required for offline TLS fixtures')
class LocalTLSIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='lab-c323-tls-')
        cls.addClassCleanup(cls.tmp.cleanup)
        folder = Path(cls.tmp.name)
        cls.cert = folder / 'cert.pem'
        cls.key = folder / 'key.pem'
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
            '-keyout', str(cls.key), '-out', str(cls.cert), '-days', '1',
            '-subj', '/CN=lab.test', '-addext', 'subjectAltName=DNS:lab.test',
        ], check=True, capture_output=True, timeout=15)
        server = ThreadingHTTPServer(('127.0.0.1', 0), LocalTLSHandler)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=cls.cert, keyfile=cls.key)
        server.socket = ctx.wrap_socket(server.socket, server_side=True)
        cls.server = server
        cls.addClassCleanup(server.server_close)
        cls.thread = threading.Thread(target=server.serve_forever, daemon=True)
        cls.thread.start()
        cls.addClassCleanup(server.shutdown)
        cls.port = server.server_address[1]

    def transport(self, hostname='lab.test', path='/robots.txt', *, trusted=True, limit=200):
        # Only the test's resolver is replaced with the local server socket.
        addresses = ((socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP,
                      ('127.0.0.1', self.port)),)
        ctx = ssl.create_default_context()
        if trusted:
            ctx.load_verify_locations(cafile=str(self.cert))
        with patch('pinned_https_transport.vetted_addresses', return_value=addresses), \
             patch('pinned_https_transport.ssl.create_default_context', return_value=ctx):
            return pinned_https_transport(f'https://{hostname}:443{path}', 2, limit)

    def test_verified_tls_with_pinned_numeric_ip_and_original_sni(self):
        result = self.transport()
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'Disallow: /private', result.body)
        self.assertEqual(result.effective_url, 'https://lab.test:443/robots.txt')

    def test_certificate_hostname_mismatch_rejected(self):
        with self.assertRaises(ssl.SSLCertVerificationError):
            self.transport(hostname='wrong.test')

    def test_untrusted_certificate_rejected(self):
        with self.assertRaises(ssl.SSLCertVerificationError):
            self.transport(trusted=False)

    def test_redirect_not_automatically_followed(self):
        result = self.transport(path='/redirect')
        self.assertEqual(result.status_code, 302)
        self.assertEqual(result.headers['location'], '/robots.txt')

    def test_declared_body_bound(self):
        with self.assertRaisesRegex(ValueError, 'declared body too large'):
            self.transport(path='/oversize', limit=20)

    def test_chunked_body_bound(self):
        with self.assertRaisesRegex(ValueError, 'response body exceeds limit'):
            self.transport(path='/chunked', limit=20)

    def test_encoded_body_rejected(self):
        with self.assertRaisesRegex(ValueError, 'encoded response unsupported'):
            self.transport(path='/encoded')

    def test_full_adapter_decision_over_verified_local_tls(self):
        from trusted_fetch_adapter import fetch_and_decide
        addresses = ((socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP,
                      ('127.0.0.1', self.port)),)
        ctx = ssl.create_default_context()
        ctx.load_verify_locations(cafile=str(self.cert))
        with patch('pinned_https_transport.vetted_addresses', return_value=addresses), \
             patch('pinned_https_transport.ssl.create_default_context', return_value=ctx):
            outcome = fetch_and_decide(
                'https://lab.test/private', 'TestBot',
                allowed_origins=frozenset({'https://lab.test:443'}),
                allow_network=True, transport=pinned_https_transport)
        self.assertEqual(outcome.status, 'disallowed')
        self.assertEqual(outcome.transport_kind, 'test_double')
        self.assertEqual(outcome.record.status_code, 200)

    def test_loopback_still_rejected_by_real_vetting(self):
        def local_resolver(*args, **kwargs):
            return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP,
                     '', ('127.0.0.1', self.port))]
        with self.assertRaisesRegex(ValueError, 'non-global'):
            vetted_addresses('lab.test', self.port, resolver=local_resolver)


if __name__ == '__main__':
    unittest.main()

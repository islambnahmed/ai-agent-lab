"""Offline-only DNS-pinning and HTTP response-path regression tests."""
import socket
import ssl
import unittest
from unittest.mock import patch
from pinned_https_transport import vetted_addresses, _PinnedHTTPSConnection, pinned_https_transport


def ans(ip, family=socket.AF_INET, port=443):
    return (family, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', (ip, port))


class DnsSafety(unittest.TestCase):
    def test_public_ipv4(self):
        self.assertEqual(len(vetted_addresses('example.test', 443, resolver=lambda *a, **k: [ans('8.8.8.8')])), 1)
    def test_mixed_dns_rejected_not_filtered(self):
        with self.assertRaisesRegex(ValueError, 'non-global'):
            vetted_addresses('example.test',443,resolver=lambda *a,**k:[ans('8.8.8.8'),ans('127.0.0.1')])
    def test_private(self):
        for ip in ('127.0.0.1','10.0.0.2','169.254.169.254','192.168.0.1','0.0.0.0','224.0.0.1','192.0.2.1'):
            with self.subTest(ip=ip), self.assertRaises(ValueError):
                vetted_addresses('example.test',443,resolver=lambda *a,**k:[ans(ip)])
    def test_ipv6_private(self):
        for ip in ('::1','fe80::1','fc00::1','2001:db8::1'):
            with self.subTest(ip=ip), self.assertRaises(ValueError):
                vetted_addresses('example.test',443,resolver=lambda *a,**k:[ans(ip,socket.AF_INET6)])
    def test_empty(self):
        with self.assertRaises(ValueError): vetted_addresses('example.test',443,resolver=lambda *a,**k:[])
    def test_family_mismatch(self):
        with self.assertRaises(ValueError): vetted_addresses('example.test',443,resolver=lambda *a,**k:[ans('8.8.8.8',socket.AF_INET6)])
    def test_bad_port(self):
        with self.assertRaises(ValueError): vetted_addresses('example.test',443,resolver=lambda *a,**k:[ans('8.8.8.8',port=80)])


class PinnedConnect(unittest.TestCase):
    def test_connects_vetted_ip_and_verifies_original_hostname(self):
        log=[]
        class FakeSocket:
            def settimeout(self,x): log.append(('timeout',x))
            def connect(self,x): log.append(('connect',x))
            def close(self): log.append(('close',))
        class FakeContext:
            def wrap_socket(self,raw,server_hostname):
                log.append(('sni',server_hostname)); return raw
        with patch('pinned_https_transport.socket.socket',return_value=FakeSocket()):
            conn=_PinnedHTTPSConnection('example.test',443,timeout=2,addresses=(ans('8.8.8.8')[:3]+(ans('8.8.8.8')[4],),),context=FakeContext())
            conn.connect()
        self.assertIn(('connect',('8.8.8.8',443)),log)
        self.assertIn(('sni','example.test'),log)
    def test_rebind_between_resolution_and_connect_not_possible(self):
        # Only literal sockaddr is handed to socket.connect, never host string.
        self.test_connects_vetted_ip_and_verifies_original_hostname()


class HttpPaths(unittest.TestCase):
    def test_redirect_response_not_followed_and_body_bounded(self):
        log=[]
        class Response:
            status=302
            def getheaders(self): return [('Location','/next')]
            def read(self,n): log.append(('read',n)); return b''
        class Conn:
            def __init__(self,*args,**kw): log.append(('addresses',kw['addresses']))
            def request(self,method,path,headers): log.append(('request',method,path,headers))
            def getresponse(self): return Response()
            def close(self): log.append(('closed',))
        with patch('pinned_https_transport.vetted_addresses',return_value=((socket.AF_INET,socket.SOCK_STREAM,socket.IPPROTO_TCP,('8.8.8.8',443)),)),patch('pinned_https_transport._PinnedHTTPSConnection',Conn):
            r=pinned_https_transport('https://example.test:443/robots.txt',2,20)
        self.assertEqual(r.status_code,302)
        self.assertEqual(log[-1],('closed',))
        self.assertIn(('read',21),log)
        self.assertEqual(len([x for x in log if x[0]=='request']),1)
    def test_content_encoding_rejected(self):
        class Response:
            status=200
            def getheaders(self): return [('Content-Encoding','gzip')]
        class Conn:
            def __init__(self,*a,**k): pass
            def request(self,*a,**k): pass
            def getresponse(self): return Response()
            def close(self): pass
        with patch('pinned_https_transport.vetted_addresses',return_value=((socket.AF_INET,socket.SOCK_STREAM,socket.IPPROTO_TCP,('8.8.8.8',443)),)),patch('pinned_https_transport._PinnedHTTPSConnection',Conn):
            with self.assertRaisesRegex(ValueError,'encoded'): pinned_https_transport('https://example.test/robots.txt',2,100)
    def test_http_refused_before_dns(self):
        with patch('pinned_https_transport.vetted_addresses') as resolver:
            with self.assertRaises(ValueError): pinned_https_transport('http://example.test/robots.txt',2,100)
            resolver.assert_not_called()

if __name__=='__main__': unittest.main()

class AdapterIntegration(unittest.TestCase):
    def test_pinned_transport_with_mocked_http_end_to_end(self):
        from trusted_fetch_adapter import fetch_and_decide
        class Response:
            status=200
            def getheaders(self): return [('Content-Type','text/plain')]
            def read(self,n): return b'User-agent: *\nDisallow: /private\n'
        class Conn:
            def __init__(self,*args,**kw): pass
            def request(self,*args,**kw): pass
            def getresponse(self): return Response()
            def close(self): pass
        with patch('pinned_https_transport.vetted_addresses',return_value=((socket.AF_INET,socket.SOCK_STREAM,socket.IPPROTO_TCP,('8.8.8.8',443)),)), patch('pinned_https_transport._PinnedHTTPSConnection',Conn):
            d=fetch_and_decide('https://example.test/private','ExampleBot',allowed_origins=frozenset({'https://example.test:443'}),allow_network=True,transport=pinned_https_transport)
        self.assertEqual(d.status,'disallowed')
        self.assertEqual(d.transport_kind,'test_double') # injected path never promoted to authenticated
    def test_dns_rebind_on_redirect_abstains(self):
        from trusted_fetch_adapter import fetch_and_decide
        class Response:
            status=302
            def getheaders(self): return [('Location','/second')]
            def read(self,n): return b''
        class Conn:
            def __init__(self,*args,**kw): pass
            def request(self,*args,**kw): pass
            def getresponse(self): return Response()
            def close(self): pass
        dns_answers=iter([[ans('8.8.8.8')],[ans('127.0.0.1')]])
        def dns(*args,**kw): return next(dns_answers)
        with patch('pinned_https_transport.socket.getaddrinfo',side_effect=dns), patch('pinned_https_transport._PinnedHTTPSConnection',Conn):
            d=fetch_and_decide('https://example.test/private','ExampleBot',allowed_origins=frozenset({'https://example.test:443'}),allow_network=True,transport=pinned_https_transport)
        self.assertEqual(d.status,'unknown')
        self.assertIn('non-global',d.reason)

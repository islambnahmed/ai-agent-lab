"""No live HTTP requests: all responses are injected deterministic fixtures."""
from dataclasses import replace
import unittest
from trusted_fetch_adapter import fetch_and_decide, TransportResponse

ROOT='https://example.test:443/robots.txt'
TARGET='https://example.test/private'
ALLOW=frozenset({'https://example.test:443'})
BODY=b'User-agent: *\nDisallow: /private\n'


def fixture(responses, calls=None):
    def send(url, timeout, limit):
        if calls is not None: calls.append((url,timeout,limit))
        result=responses[url]
        if isinstance(result, Exception): raise result
        return result
    return send


def response(url=ROOT, status=200, body=BODY, headers=None):
    return TransportResponse(status,url,headers or {},body)


def decide(responses=None, target=TARGET, **kw):
    return fetch_and_decide(target,'ExampleBot',allowed_origins=ALLOW,
                            allow_network=True,transport=fixture(responses or {ROOT:response()}),**kw)

class AdapterTests(unittest.TestCase):
    def test_disallowed(self):
        d=decide(); self.assertEqual(d.status,'disallowed'); self.assertEqual(d.transport_kind,'test_double')
        self.assertTrue(d.decision.evidence_consistent)
    def test_allowed(self): self.assertEqual(decide(target='https://example.test/public').status,'allowed')
    def test_network_disabled_default(self):
        calls=[]
        d=fetch_and_decide(TARGET,'Bot',allowed_origins=ALLOW,transport=fixture({},calls))
        self.assertEqual(d.status,'unknown'); self.assertFalse(calls)
    def test_origin_not_authorized(self):
        d=decide(target='https://different.test/private'); self.assertEqual(d.status,'unknown')
    def test_http_not_authorized(self): self.assertEqual(decide(target='http://example.test/private').status,'unknown')
    def test_credentials_rejected(self): self.assertEqual(decide(target='https://u@example.test/private').status,'unknown')
    def test_invalid_origin_allowlist(self):
        self.assertEqual(fetch_and_decide(TARGET,'Bot',allowed_origins=['https://example.test:443'],allow_network=True).status,'unknown')
    def test_bad_timeout(self): self.assertEqual(decide(timeout_seconds=float('nan')).status,'unknown')
    def test_bad_body_limit(self): self.assertEqual(decide(max_body_bytes=0).status,'unknown')
    def test_oversize(self): self.assertEqual(decide({ROOT:response(body=BODY*50000)},max_body_bytes=100).status,'unknown')
    def test_bad_encoding(self): self.assertEqual(decide({ROOT:response(headers={'Content-Encoding':'gzip'})}).status,'unknown')
    def test_status_404_unknown(self): self.assertEqual(decide({ROOT:response(status=404)}).status,'unknown')
    def test_status_500_unknown(self): self.assertEqual(decide({ROOT:response(status=500)}).status,'unknown')
    def test_unrecorded_redirect(self):
        self.assertEqual(decide({ROOT:response(url='https://example.test:443/other')}).status,'unknown')
    def test_same_origin_relative_redirect(self):
        nxt='https://example.test:443/r2'
        d=decide({ROOT:response(status=302,headers={'Location':'/r2'}),nxt:response(url=nxt)})
        self.assertEqual(d.status,'disallowed'); self.assertEqual(len(d.record.redirects),1)
    def test_cross_origin_redirect(self):
        d=decide({ROOT:response(status=302,headers={'Location':'https://evil.test/robots.txt'})})
        self.assertEqual(d.status,'unknown')
    def test_https_downgrade(self):
        self.assertEqual(decide({ROOT:response(status=301,headers={'Location':'http://example.test/robots.txt'})}).status,'unknown')
    def test_redirect_missing_location(self):
        self.assertEqual(decide({ROOT:response(status=302)}).status,'unknown')
    def test_location_newline_rejected(self):
        self.assertEqual(decide({ROOT:response(status=302,headers={'Location':'/ok\n'})}).status,'unknown')
    def test_location_fragment_rejected(self):
        self.assertEqual(decide({ROOT:response(status=302,headers={'Location':'/ok#frag'})}).status,'unknown')
    def test_location_backslash_rejected(self):
        self.assertEqual(decide({ROOT:response(status=302,headers={'Location':'\\evil.test'})}).status,'unknown')
    def test_redirect_loop(self):
        nxt='https://example.test:443/r2'
        d=decide({ROOT:response(status=302,headers={'Location':'/r2'}),nxt:response(url=nxt,status=302,headers={'Location':'/robots.txt'})})
        self.assertEqual(d.status,'unknown')
    def test_redirect_limit(self):
        nxt='https://example.test:443/r2'
        d=decide({ROOT:response(status=302,headers={'Location':'/r2'}),nxt:response(url=nxt)},max_redirects=0)
        self.assertEqual(d.status,'unknown')
    def test_transport_exception(self): self.assertEqual(decide({ROOT:TimeoutError('offline timeout')}).status,'unknown')
    def test_fabricated_body_not_network_authenticated(self):
        fake=b'User-agent: *\nAllow: /private\n'
        d=decide({ROOT:response(body=fake)})
        self.assertEqual(d.status,'allowed')
        self.assertEqual(d.transport_kind,'test_double')
        # A test-double response is NOT independent proof of an HTTP origin.
    def test_invalid_utf8(self): self.assertEqual(decide({ROOT:response(body=b'\xff')}).status,'unknown')
    def test_fake_implicit_redirect_rejected(self):
        d=decide({ROOT:response(url='https://example.test:443/other',status=200)})
        self.assertEqual(d.status,'unknown')
    def test_redirect_chain_evidence(self):
        nxt='https://example.test:443/r2'
        d=decide({ROOT:response(status=307,headers={'Location':'/r2'}),nxt:response(url=nxt)})
        self.assertEqual(d.record.redirects[0].status_code,307)
        self.assertEqual(d.record.final_url,nxt)

if __name__=='__main__': unittest.main()

class TransportConstructionTests(unittest.TestCase):
    def test_stdlib_https_no_implicit_redirects_or_environment_proxy(self):
        from unittest.mock import patch
        from urllib.request import ProxyHandler
        from trusted_fetch_adapter import stdlib_https_transport, _NoRedirect
        captured={}
        class DummyResponse:
            headers={'Content-Type':'text/plain'}
            code=200
            def geturl(self): return ROOT
            def read(self, n): captured['read_limit']=n; return BODY
            def close(self): captured['closed']=True
        class DummyOpener:
            def open(self, request, timeout):
                captured['request']=request
                captured['timeout']=timeout
                return DummyResponse()
        def fake_build(*handlers):
            captured['handlers']=handlers
            return DummyOpener()
        with patch('trusted_fetch_adapter.build_opener',side_effect=fake_build):
            out=stdlib_https_transport(ROOT,2.0,1000)
        self.assertEqual(out.body,BODY)
        self.assertEqual(captured['read_limit'],1001)
        self.assertTrue(captured['closed'])
        self.assertEqual(captured['request'].get_header('Accept-encoding'),'identity')
        self.assertTrue(any(isinstance(h,_NoRedirect) for h in captured['handlers']))
        self.assertTrue(any(isinstance(h,ProxyHandler) and h.proxies=={} for h in captured['handlers']))
    def test_stdlib_transport_rejects_http_without_request(self):
        from trusted_fetch_adapter import stdlib_https_transport
        with self.assertRaises(ValueError):
            stdlib_https_transport('http://example.test/robots.txt',1.0,100)

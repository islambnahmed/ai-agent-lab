"""Offline synthetic regression suite. PYTHONPATH must include c318, c319, c320."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import unittest

from provenance_gate import RedirectHop, RobotsFetchRecord, evaluate_record

NOW = datetime(2026, 10, 23, 9, 20, tzinfo=timezone.utc)
ROOT = 'https://example.test/robots.txt'
TARGET = 'https://example.test/private/1'
BODY = b'User-agent: *\nDisallow: /private\n'


def record(**changes):
    fields = dict(requested_url=ROOT, final_url=ROOT, redirects=(),
                  status_code=200, body=BODY,
                  body_sha256=hashlib.sha256(BODY).hexdigest(),
                  fetched_at=NOW-timedelta(seconds=60))
    fields.update(changes)
    return RobotsFetchRecord(**fields)


class ProvenanceTests(unittest.TestCase):
    def decide(self, expected, rec=None, target=TARGET, **kw):
        result = evaluate_record(rec if rec is not None else record(), 'ExampleBot', target,
                                 now=NOW, **kw)
        self.assertEqual(result.status, expected, result)
        return result

    def test_same_origin_disallowed(self):
        d = self.decide('disallowed')
        self.assertTrue(d.evidence_consistent)
        self.assertEqual(d.chain_length, 0)
    def test_same_origin_allowed(self): self.decide('allowed', target='https://example.test/public')
    def test_source_host_case_default_port(self):
        self.decide('disallowed', record(requested_url='HTTPS://EXAMPLE.TEST:443/robots.txt',
                                          final_url='HTTPS://EXAMPLE.TEST:443/robots.txt'))
    def test_robots_query_forbidden(self): self.decide('unknown', record(requested_url=ROOT+'?v=1', final_url=ROOT+'?v=1'))
    def test_target_other_host(self): self.decide('unknown', target='https://other.test/private')
    def test_target_other_scheme(self): self.decide('unknown', target='http://example.test/private')
    def test_target_other_port(self): self.decide('unknown', target='https://example.test:444/private')
    def test_target_credentials(self): self.decide('unknown', target='https://user@example.test/private')
    def test_target_fragment(self): self.decide('unknown', target=TARGET+'#a')
    def test_body_digest_mismatch(self):
        d = self.decide('unknown', record(body=BODY+b'Allow: /private\n'))
        self.assertIn('hash mismatch', d.reason)
    def test_uppercase_digest_rejected(self): self.decide('unknown', record(body_sha256=hashlib.sha256(BODY).hexdigest().upper()))
    def test_short_digest_rejected(self): self.decide('unknown', record(body_sha256='1234'))
    def test_wrong_body_type(self): self.decide('unknown', record(body=BODY.decode()))
    def test_non_utf8_body(self):
        b = b'\xff\xfe'
        self.decide('unknown', record(body=b, body_sha256=hashlib.sha256(b).hexdigest()))
    def test_utf8_bom_body(self):
        b = b'\xef\xbb\xbf'+BODY
        self.decide('disallowed', record(body=b, body_sha256=hashlib.sha256(b).hexdigest()))
    def test_empty_body_defaults_allow(self):
        self.decide('allowed', record(body=b'', body_sha256=hashlib.sha256(b'').hexdigest()))
    def test_stale_body(self): self.decide('unknown', record(fetched_at=NOW-timedelta(days=2)))
    def test_exact_ttl_boundary(self): self.decide('disallowed', record(fetched_at=NOW-timedelta(days=1)))
    def test_future_timestamp(self): self.decide('unknown', record(fetched_at=NOW+timedelta(seconds=1)))
    def test_naive_timestamp(self): self.decide('unknown', record(fetched_at=NOW.replace(tzinfo=None)))
    def test_naive_now(self):
        d=evaluate_record(record(), 'ExampleBot', TARGET, now=NOW.replace(tzinfo=None))
        self.assertEqual(d.status, 'unknown')
    def test_invalid_max_age(self): self.decide('unknown', max_age_seconds=0)
    def test_invalid_redirect_bound(self): self.decide('unknown', max_redirects=-1)
    def test_non_200_final_status(self): self.decide('unknown', record(status_code=404))
    def test_200_boolean_not_accepted(self): self.decide('unknown', record(status_code=True))
    def test_same_origin_redirect(self):
        final='https://example.test/seo/robots-v2.txt'
        rec=record(final_url=final, redirects=(RedirectHop(ROOT, 302, final),))
        d=self.decide('disallowed', rec)
        self.assertEqual(d.chain_length, 1)
    def test_two_hops(self):
        mid='https://example.test/a'
        final='https://example.test/b'
        rec=record(final_url=final, redirects=(RedirectHop(ROOT, 301, mid), RedirectHop(mid, 308, final)))
        self.decide('disallowed', rec)
    def test_cross_origin_redirect(self):
        final='https://cdn.test/robots.txt'
        rec=record(final_url=final, redirects=(RedirectHop(ROOT, 302, final),))
        d=self.decide('unknown', rec)
        self.assertIn('cross-origin', d.reason)
    def test_redirect_wrong_scheme(self):
        final='http://example.test/robots.txt'
        self.decide('unknown', record(final_url=final, redirects=(RedirectHop(ROOT, 301, final),)))
    def test_redirect_wrong_port(self):
        final='https://example.test:444/robots.txt'
        self.decide('unknown', record(final_url=final, redirects=(RedirectHop(ROOT, 301, final),)))
    def test_redirect_chain_gap(self):
        final='https://example.test/b'
        self.decide('unknown', record(final_url=final, redirects=(RedirectHop('https://example.test/other', 301, final),)))
    def test_redirect_non_3xx(self):
        final='https://example.test/b'
        self.decide('unknown', record(final_url=final, redirects=(RedirectHop(ROOT, 200, final),)))
    def test_redirect_loop(self):
        mid='https://example.test/b'
        self.decide('unknown', record(final_url=ROOT, redirects=(RedirectHop(ROOT, 302, mid), RedirectHop(mid, 301, ROOT))))
    def test_redirect_final_mismatch(self):
        mid='https://example.test/b'
        self.decide('unknown', record(final_url='https://example.test/c', redirects=(RedirectHop(ROOT, 302, mid),)))
    def test_redirect_too_long(self):
        hops=[]
        prev=ROOT
        for i in range(6):
            dest=f'https://example.test/r{i}'
            hops.append(RedirectHop(prev, 302, dest))
            prev=dest
        self.decide('unknown', record(final_url=prev, redirects=tuple(hops)))
    def test_redirect_relative_url_rejected(self):
        self.decide('unknown', record(final_url='/new', redirects=(RedirectHop(ROOT, 302, '/new'),)))
    def test_final_without_redirect_mismatch(self):
        self.decide('unknown', record(final_url='https://example.test/other'))
    def test_redirect_ambiguous_authority(self):
        final='https://user@example.test/robots.txt'
        self.decide('unknown', record(final_url=final, redirects=(RedirectHop(ROOT, 302, final),)))
    def test_invalid_product_token_abstains(self):
        d=evaluate_record(record(), 'bot/evil', TARGET, now=NOW)
        self.assertEqual(d.status, 'unknown')
        self.assertTrue(d.evidence_consistent)
    def test_invalid_record_type(self):
        self.assertEqual(evaluate_record({}, 'Bot', TARGET, now=NOW).status, 'unknown')

if __name__ == '__main__':
    unittest.main()

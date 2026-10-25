"""Exp439: conservative, local-only semantic preparation and bound execution.

Toy adapters model two *possible* downstream interpretations; they do not claim
that GitHub or Notion themselves parse paths/JSON this way. No network I/O.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from threading import Lock
import json
import re
import time
import unicodedata
import uuid

REPO = 'islambnahmed/ai-agent-lab'
NOTION_ROOT = '3e6dc50f-dddb-8157-a972-eb2b2f4d53db'

class Rejected(ValueError):
    pass

@dataclass(frozen=True)
class Request:
    surface: str
    target: str
    operation: str
    path: str = ''
    branch: str = ''
    payload: str = ''

@dataclass(frozen=True)
class Prepared:
    adapter: str
    revision: str
    method: str
    target: str
    path: str
    branch: str
    wire_body: bytes

    def digest(self) -> str:
        # Length-delimited encoding: JSON serializes byte body as hex, not as an
        # ambiguously concatenated sequence of fields.
        record = dict(adapter=self.adapter, revision=self.revision,
                      method=self.method, target=self.target, path=self.path,
                      branch=self.branch, wire_body_hex=self.wire_body.hex())
        return sha256(json.dumps(record, sort_keys=True, separators=(',', ':'),
                                 ensure_ascii=True).encode('ascii')).hexdigest()


def _reject_duplicate_keys(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise Rejected('duplicate JSON key: ' + key)
        out[key] = value
    return out


def _strict_json(raw: str):
    if not isinstance(raw, str) or len(raw) > 65536:
        raise Rejected('payload must be a bounded string')
    try:
        obj = json.loads(raw, object_pairs_hook=_reject_duplicate_keys,
                         parse_constant=lambda _: (_ for _ in ()).throw(Rejected('non-finite JSON')))
    except (ValueError, TypeError) as e:
        raise Rejected(str(e)) from e
    return obj


def _canonical_repo_path(path: str) -> str:
    if not isinstance(path, str) or not path:
        raise Rejected('missing path')
    if unicodedata.normalize('NFC', path) != path:
        raise Rejected('non-NFC path')
    if '%' in path or '\\' in path or any(ord(c) < 32 or ord(c) == 127 for c in path):
        raise Rejected('ambiguous path encoding')
    if any(part in ('', '.', '..') for part in path.split('/')):
        raise Rejected('noncanonical path segments')
    if not re.fullmatch(r'experiments/khepri/[A-Za-z0-9_./-]+\.md', path):
        raise Rejected('path outside sample write allowlist')
    return path


class Adapter:
    """Prepare the exact bytes/route the simulated executor will use."""
    def __init__(self, revision='v1'):
        self.revision = revision

    def prepare(self, r: Request) -> Prepared:
        if not isinstance(r, Request):
            raise Rejected('bad request')
        if not all(isinstance(v, str) for v in vars(r).values()):
            raise Rejected('non-string request field')
        if r.surface == 'github':
            if r.target != REPO or r.operation != 'create_file':
                raise Rejected('unauthorized repository or method')
            if (not re.fullmatch(r'khepri/[a-z0-9][a-z0-9/_-]*', r.branch)
                    or '//' in r.branch):
                raise Rejected('unauthorized branch')
            path = _canonical_repo_path(r.path)
            return Prepared('github', self.revision, 'create_file', r.target,
                            path, r.branch, r.payload.encode('utf-8'))
        if r.surface == 'notion':
            if (r.target != NOTION_ROOT or r.operation != 'append_child'
                    or r.path or r.branch):
                raise Rejected('unauthorized notion target or method')
            obj = _strict_json(r.payload)
            if (not isinstance(obj, dict) or set(obj) != {'kind', 'text'}
                    or obj['kind'] != 'paragraph' or not isinstance(obj['text'], str)
                    or len(obj['text']) > 10000):
                raise Rejected('unexpected notion payload schema')
            try:
                body = json.dumps(obj, sort_keys=True, ensure_ascii=False,
                                  separators=(',', ':')).encode('utf-8')
            except UnicodeError as e:
                raise Rejected('invalid Unicode payload') from e
            return Prepared('notion', self.revision, 'append_child', r.target,
                            '', '', body)
        raise Rejected('unknown surface')


@dataclass(frozen=True)
class Permit:
    token: str
    digest: str
    expires: float


class BoundExecutor:
    def __init__(self, clock=None):
        self._clock = clock or time.monotonic
        self._ledger = {}
        self._lock = Lock()
        self.effects = []  # simulated only

    def issue(self, r: Request, adapter: Adapter, ttl=60) -> Permit:
        if ttl <= 0:
            raise Rejected('nonpositive ttl')
        p = adapter.prepare(r)
        with self._lock:
            token = uuid.uuid4().hex
            expiry = self._clock() + ttl
            self._ledger[token] = (p.digest(), expiry)
            return Permit(token, p.digest(), expiry)

    def execute(self, permit: Permit, r: Request, adapter: Adapter) -> bool:
        if not isinstance(permit, Permit):
            return False
        try:
            p = adapter.prepare(r)
        except (Rejected, UnicodeError):
            return False
        with self._lock:
            record = self._ledger.get(permit.token)
            if (record is None or record != (permit.digest, permit.expires)
                    or self._clock() > permit.expires or p.digest() != permit.digest):
                return False
            del self._ledger[permit.token]
            self.effects.append(p)  # no external side effect
            return True


def weak_first_wins(raw: str) -> dict:
    """Deliberately flawed checker for demonstration only."""
    return json.loads(raw, object_pairs_hook=lambda pairs: {k: next(v for kk, v in pairs if kk == k) for k, _ in pairs})


def toy_last_wins(raw: str) -> dict:
    """Synthetic downstream JSON parser; not a claim about Notion's API."""
    return json.loads(raw)

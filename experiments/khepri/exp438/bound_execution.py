"""Exp438: local-only execution-bound authorization with a single-use permit.

No external GitHub/Drive/Notion writes. The caller must not be able to mutate
Gate's private ledger or impersonate its trusted API in a real deployment.
"""
from __future__ import annotations
from dataclasses import dataclass
from threading import Lock
from hashlib import sha256
import json
import re
import uuid
import time

REPO = 'islambnahmed/ai-agent-lab'
DRIVE_ROOT = '1-SZxzumsAh2zDYfo9MHwVHVb-r8vMaqU'
NOTION_ROOT = '3e6dc50f-dddb-8157-a972-eb2b2f4d53db'

@dataclass(frozen=True)
class Action:
    surface: str
    operation: str
    target: str
    path: str = ''
    branch: str = ''
    payload: str = ''

@dataclass(frozen=True)
class Permit:
    token: str
    digest: str
    policy_revision: int
    expires_at: int


def authorized(a: Action) -> bool:
    """Conservative lab-only allowlist; real tool boundaries need own validation."""
    if not isinstance(a, Action) or not all(isinstance(v, str) for v in vars(a).values()):
        return False
    if a.surface == 'github':
        if a.target != REPO or not re.fullmatch(r'experiments/khepri/[a-z0-9_/-]+\.md', a.path):
            return False
        if a.operation == 'create_file':
            return bool(re.fullmatch(r'khepri/[a-z0-9][a-z0-9/_-]*', a.branch)) and '..' not in a.path.split('/')
        return a.operation == 'read' and a.payload == ''
    if a.surface == 'drive':
        return a.target == DRIVE_ROOT and a.branch == '' and a.path == 'lab-note.md' and a.operation == 'create_file'
    if a.surface == 'notion':
        return a.target == NOTION_ROOT and a.branch == '' and a.path == '' and a.operation == 'append_child'
    return False


def fingerprint(a: Action) -> str:
    """Bind ALL action fields, including body, via unambiguous serialization."""
    return sha256(json.dumps(vars(a), sort_keys=True, ensure_ascii=True,
                             separators=(',', ':')).encode('utf-8')).hexdigest()


class Gate:
    def __init__(self, policy_revision: int = 1, clock=None):
        self.policy_revision = policy_revision
        self._clock = clock if clock is not None else time.monotonic
        self._ledger: dict[str, tuple[str, int, int]] = {}
        self._lock = Lock()
        self.executed: list[Action] = []

    def issue(self, a: Action, ttl: int = 60) -> Permit | None:
        if not authorized(a) or ttl <= 0:
            return None
        digest = fingerprint(a)
        with self._lock:
            token = uuid.uuid4().hex
            expires_at = self._clock() + ttl
            self._ledger[token] = (digest, self.policy_revision, expires_at)
            return Permit(token, digest, self.policy_revision, expires_at)

    def execute(self, p: Permit, a: Action) -> bool:
        """Atomic check-and-consume before simulated execution (no I/O)."""
        if not isinstance(p, Permit):
            return False
        if not authorized(a):
            return False
        digest = fingerprint(a)
        with self._lock:
            record = self._ledger.get(p.token)
            if record is None:
                return False
            expected_digest, revision, expiry = record
            if (revision != self.policy_revision or p.policy_revision != revision
                    or self._clock() > expiry or p.expires_at != expiry
                    or digest != expected_digest or p.digest != expected_digest):
                return False
            del self._ledger[p.token]
            self.executed.append(a)
            return True


def naive_execute(approved: Action, actual: Action) -> bool:
    """Weak integration: checks approved request, executes unbound actual request."""
    return authorized(approved)  # ignores actual

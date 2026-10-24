"""Exp420: simulated tool-side optimistic concurrency approval, no real writes.

This models one-use approval bound to (plan, payload, resource version).
It does NOT implement cryptographic identity or external tool authorization.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from hmac import compare_digest
from threading import RLock

REPO = 'islambnahmed/ai-agent-lab'
BRANCH = 'khepri/exp420-state-bound-20261024'
PREFIX = 'experiments/khepri/exp420/'


@dataclass(frozen=True)
class Plan:
    operation: str
    repository: str
    branch: str
    path: str


@dataclass(frozen=True)
class Outcome:
    accepted: bool
    reason: str
    version: int | None = None


def fields(plan: object) -> tuple[str, str, str, str] | None:
    if type(plan) is not Plan:
        return None
    parts = (plan.operation, plan.repository, plan.branch, plan.path)
    if any(type(p) is not str for p in parts):
        return None
    return parts


def in_scope(plan: object) -> bool:
    v = fields(plan)
    if v is None:
        return False
    op, repo, branch, path = v
    if (op, repo, branch) != ('write', REPO, BRANCH):
        return False
    if not path.startswith(PREFIX) or len(path.encode('utf-8')) > 240:
        return False
    segments = path.split('/')
    return all(segment and segment not in ('.', '..', '.git', '.env')
               and not segment.startswith('.git') and
               all(c.isascii() and (c.isalnum() or c in '._-') for c in segment)
               for segment in segments)


class FakeStore:
    """Version increments on every successful write, including ABA and no-op writes."""
    def __init__(self):
        self._lock = RLock()
        self._data: dict[str, tuple[bytes, int]] = {}

    def seed(self, path: str, data: bytes):
        if type(path) is not str or type(data) is not bytes:
            raise TypeError('primitive seed required')
        with self._lock:
            _, version = self._data.get(path, (b'', 0))
            self._data[path] = (data, version + 1)

    def snapshot(self, path: str) -> tuple[bytes | None, int]:
        with self._lock:
            return self._data.get(path, (None, 0))

    def tool_write(self, path: str, data: bytes, expected_version: int | None) -> Outcome:
        """The *tool boundary* checks version and commits while holding one lock."""
        with self._lock:
            _, version = self._data.get(path, (None, 0))
            if expected_version is not None and version != expected_version:
                return Outcome(False, 'stale resource version', version)
            self._data[path] = (data, version + 1)
            return Outcome(True, 'simulated write', version + 1)


class Approver:
    def __init__(self, store: FakeStore, *, bind_version: bool):
        self._store = store
        self._bind_version = bind_version
        self._pending: dict[object, tuple[tuple[str, str, str, str], str, int]] = {}

    def issue(self, plan: Plan, approved_bytes: bytes) -> object:
        if not in_scope(plan) or type(approved_bytes) is not bytes:
            raise ValueError('invalid approved action')
        # Copy immutable primitives, never retain caller-owned Plan object.
        v = fields(plan)
        assert v is not None
        _, version = self._store.snapshot(v[3])
        token = object()
        self._pending[token] = (v, sha256(approved_bytes).hexdigest(), version)
        return token

    def redeem(self, receipt: object, requested: object, payload: object) -> Outcome:
        if type(receipt) is not object:
            return Outcome(False, 'invalid receipt')
        approved = self._pending.pop(receipt, None)
        if approved is None:
            return Outcome(False, 'unknown or spent receipt')
        approved_fields, digest, expected_version = approved
        if not in_scope(requested) or fields(requested) != approved_fields:
            return Outcome(False, 'plan mismatch')
        if type(payload) is not bytes or not compare_digest(sha256(payload).hexdigest(), digest):
            return Outcome(False, 'payload mismatch')
        # Only the version-bound variant guards against intervening changes.
        return self._store.tool_write(approved_fields[3], payload,
                                      expected_version if self._bind_version else None)


def plan(name: str = 'sample.txt') -> Plan:
    return Plan('write', REPO, BRANCH, PREFIX + name)

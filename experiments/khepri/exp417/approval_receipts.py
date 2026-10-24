"""In-process, simulated one-use action approvals for an AI Agent Lab experiment.

No external writes. This is a *structural* boundary: trusted composition must keep
Issuer away from the untrusted planner. Python object identity is NOT a security
primitive against arbitrary code execution or reflection in the same process.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import re
import unicodedata

REPO = 'islambnahmed/ai-agent-lab'
BRANCH = 'khepri/exp417-approval-receipts-20261024'
PREFIX = 'experiments/khepri/exp417/'
_COMPONENT = re.compile(r'^[A-Za-z0-9_.-]+$')


@dataclass(frozen=True)
class Plan:
    operation: str
    repository: str
    branch: str
    path: str


@dataclass(frozen=True)
class Result:
    accepted: bool
    reason: str
    simulated_action: tuple[str, str, str, str] | None = None


def in_scope(plan: Plan) -> bool:
    if not isinstance(plan, Plan):
        return False
    values = (plan.operation, plan.repository, plan.branch, plan.path)
    if not all(type(v) is str for v in values):
        return False
    if (plan.operation != 'write' or plan.repository != REPO or
            plan.branch != BRANCH or not plan.path.startswith(PREFIX) or
            len(plan.path.encode('utf-8')) > 240 or
            unicodedata.normalize('NFKC', plan.path) != plan.path):
        return False
    parts = plan.path.split('/')
    return all(p not in ('', '.', '..', '.git', '.env') and
               not p.startswith('.git') and _COMPONENT.fullmatch(p)
               for p in parts)


class _State:
    def __init__(self):
        self.pending: dict[object, tuple[Plan, str]] = {}
        self.used: set[object] = set()


class Issuer:
    """Trusted-side interface. Do not expose to a planner parsing untrusted data."""
    def __init__(self, state: _State):
        self._state = state

    def issue(self, trusted_plan: Plan, approved_payload: bytes) -> object:
        if not in_scope(trusted_plan):
            raise ValueError('plan not in authorized experiment scope')
        if type(approved_payload) is not bytes:
            raise TypeError('payload must be immutable bytes')
        receipt = object()  # opaque identity, not a cryptographic token
        self._state.pending[receipt] = (trusted_plan, sha256(approved_payload).hexdigest())
        return receipt


class Executor:
    """Untrusted-planner-facing interface. Never executes real tool calls."""
    def __init__(self, state: _State):
        self._state = state

    def simulate(self, receipt: object, requested: Plan, payload: bytes) -> Result:
        # Consume on the first attempt, even a mismatch: prevents replay, but a
        # leaked receipt can be exhausted (denial-of-service, not integrity loss).
        approved = self._state.pending.pop(receipt, None)
        if approved is None:
            return Result(False, 'unknown or spent approval')
        self._state.used.add(receipt)
        if not in_scope(requested) or requested != approved[0]:
            return Result(False, 'request differs from approved plan')
        if type(payload) is not bytes:
            return Result(False, 'invalid payload type')
        if sha256(payload).hexdigest() != approved[1]:
            return Result(False, 'payload differs from approved bytes')
        return Result(True, 'simulated approval consumed',
                      (requested.operation, requested.repository, requested.branch, requested.path))


def new_runtime() -> tuple[Issuer, Executor]:
    """Trusted composition root. In production, isolate issuance by process/API."""
    state = _State()
    return Issuer(state), Executor(state)


def scope_only(requested: Plan, payload: bytes) -> bool:
    """Deliberately vulnerable comparator: no approval provenance or payload binding."""
    return in_scope(requested) and type(payload) is bytes


def path_only_approval(approved: Plan, requested: Plan, payload: bytes) -> bool:
    """Deliberately weak comparator: approves path, not the content written."""
    return in_scope(approved) and requested == approved and type(payload) is bytes

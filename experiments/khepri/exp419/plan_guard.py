"""Exp419: simulated approval plan-type guard. No external actions.

Only protects against subclass-controlled equality/attribute behavior in this
single-process model; not a production authorization or isolation boundary.
"""
from __future__ import annotations
from hashlib import sha256
from hmac import compare_digest
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
for _sibling in ('exp417', 'exp418'):
    _path = str(_ROOT / _sibling)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from approval_receipts import Executor, Issuer, Plan, Result, in_scope, new_runtime


class PlanGuardIssuer(Issuer):
    def issue(self, trusted_plan: Plan, approved_payload: bytes) -> object:
        if type(trusted_plan) is not Plan:
            raise TypeError('approval plan must be exactly Plan')
        # Snapshot fields: frozen dataclasses can still be mutated via object.__setattr__.
        snapshot = Plan(trusted_plan.operation, trusted_plan.repository,
                        trusted_plan.branch, trusted_plan.path)
        return super().issue(snapshot, approved_payload)


class PlanGuardExecutor(Executor):
    def simulate(self, receipt: object, requested: object, payload: object) -> Result:
        # First reject receipt subclasses before touching a dictionary key.
        if type(receipt) is not object:
            return Result(False, 'invalid receipt type')
        approved = self._state.pending.pop(receipt, None)
        if approved is None:
            return Result(False, 'unknown or spent approval')
        self._state.used.add(receipt)
        plan, expected_digest = approved
        # Reject subclass-provided equality and dynamic attribute behavior.
        # Preserve exp417's consume-on-first-attempt behavior for real receipts.
        if type(requested) is not Plan or type(plan) is not Plan:
            return Result(False, 'invalid plan type')
        if not in_scope(plan) or not in_scope(requested):
            return Result(False, 'plan outside authorized scope')
        approved_fields = (plan.operation, plan.repository, plan.branch, plan.path)
        requested_fields = (requested.operation, requested.repository, requested.branch, requested.path)
        if requested_fields != approved_fields:
            return Result(False, 'request differs from approved plan')
        if type(payload) is not bytes:
            return Result(False, 'invalid payload type')
        if not compare_digest(sha256(payload).hexdigest(), expected_digest):
            return Result(False, 'payload differs from approved bytes')
        return Result(True, 'simulated approval consumed', approved_fields)


def new_guard_runtime() -> tuple[PlanGuardIssuer, PlanGuardExecutor]:
    _, executor = new_runtime()
    return PlanGuardIssuer(executor._state), PlanGuardExecutor(executor._state)

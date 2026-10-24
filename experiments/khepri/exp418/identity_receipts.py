"""Exp418: strict-identity adapter for exp417's simulated approval receipts.

This is NOT a process boundary, an authentication protocol, or an LLM security
claim. It only prevents arbitrary user objects from participating in Python
mapping equality/hash resolution. The trusted issuer still creates `object()`.
"""
from __future__ import annotations
import sys
from pathlib import Path

_EXP417 = Path(__file__).resolve().parents[1] / 'exp417'
if str(_EXP417) not in sys.path:
    sys.path.insert(0, str(_EXP417))

from approval_receipts import Executor, Issuer, Result, new_runtime  # noqa: E402


class StrictExecutor(Executor):
    def simulate(self, receipt: object, requested: object, payload: object) -> Result:
        # Issuer.issue creates *exactly* built-in object(), not subclasses.
        # This check precedes dict.pop, so no attacker __hash__/__eq__ runs.
        if type(receipt) is not object:
            return Result(False, 'invalid receipt type')
        return super().simulate(receipt, requested, payload)


def new_strict_runtime() -> tuple[Issuer, StrictExecutor]:
    issuer, executor = new_runtime()
    return issuer, StrictExecutor(executor._state)

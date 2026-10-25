"""Exp442: cancellation linearization at a participating idempotent sink.

All effects are SQLite-local simulation. A real remote service must implement
an equivalent atomic cancel/effect decision; this module does not grant it.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path


def connect(path: str) -> sqlite3.Connection:
    db = sqlite3.connect(path, isolation_level=None, timeout=5)
    db.execute('PRAGMA busy_timeout=5000')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE IF NOT EXISTS effects (id TEXT PRIMARY KEY, payload BLOB NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS fences (id TEXT PRIMARY KEY)')
    return db


def apply_guarded(db: sqlite3.Connection, op_id: str, payload: bytes) -> str:
    """Linearizable sink decision: applied, duplicate, or fenced."""
    db.execute('BEGIN IMMEDIATE')
    try:
        if db.execute('SELECT 1 FROM fences WHERE id=?', (op_id,)).fetchone():
            result = 'fenced'
        else:
            existing = db.execute('SELECT payload FROM effects WHERE id=?', (op_id,)).fetchone()
            if existing is None:
                db.execute('INSERT INTO effects VALUES (?,?)', (op_id, payload))
                result = 'applied'
            elif existing == (payload,):
                result = 'duplicate'
            else:
                raise ValueError('operation ID reused with different payload')
        db.execute('COMMIT')
        return result
    except BaseException:
        db.execute('ROLLBACK')
        raise


def cancel_guarded(db: sqlite3.Connection, op_id: str) -> str:
    """Durable cancellation barrier: cancelled only if no effect has committed."""
    db.execute('BEGIN IMMEDIATE')
    try:
        if db.execute('SELECT 1 FROM effects WHERE id=?', (op_id,)).fetchone():
            result = 'too_late'
        else:
            db.execute('INSERT OR IGNORE INTO fences VALUES (?)', (op_id,))
            result = 'cancelled'
        db.execute('COMMIT')
        return result
    except BaseException:
        db.execute('ROLLBACK')
        raise


def effect_count(db: sqlite3.Connection, op_id: str) -> int:
    return db.execute('SELECT COUNT(*) FROM effects WHERE id=?', (op_id,)).fetchone()[0]


def enumerate_interleavings(left: tuple[str, ...], right: tuple[str, ...]):
    if not left:
        yield right
    elif not right:
        yield left
    else:
        for tail in enumerate_interleavings(left[1:], right):
            yield (left[0],) + tail
        for tail in enumerate_interleavings(left, right[1:]):
            yield (right[0],) + tail


def evaluate(schedule: tuple[str, ...], guarded: bool) -> dict:
    """Abstract atomic-step model. Validation is deliberately separate from effect."""
    verified = False
    fence = False
    effect = False
    cancel_success = False
    for step in schedule:
        if step == 'verify':
            # The old wrapper rejects a claim if cancellation already finalized,
            # but cannot stop a previously validated dispatch in flight.
            verified = not cancel_success
        elif step == 'effect':
            if verified and (not guarded or not fence):
                effect = True
        elif step == 'cancel':
            if guarded:
                if not effect:
                    fence = True
                    cancel_success = True
            else:
                cancel_success = True  # naive outbox-only cancellation
        elif step == 'finalize':
            pass  # only durability of the fence can justify success
        else:
            raise ValueError(step)
    return {'effect': effect, 'cancel_success': cancel_success,
            'violation': effect and cancel_success}


def check_schedules(guarded: bool) -> dict:
    left = ('verify', 'effect')
    right = ('cancel', 'finalize') if guarded else ('cancel',)
    schedules = list(enumerate_interleavings(left, right))
    violations = [s for s in schedules if evaluate(s, guarded)['violation']]
    return {'schedules': len(schedules), 'violations': len(violations),
            'counterexamples': [list(s) for s in violations]}

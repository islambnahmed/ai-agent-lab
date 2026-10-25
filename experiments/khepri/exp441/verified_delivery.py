"""Exp441: receipt-gated delivery wrapper around exp440's outbox simulator.

Two separate SQLite files model independent durable outbox and destination.
No network calls; not a security boundary against malicious code with DB access.
"""
from __future__ import annotations
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "exp440"))
from durable_delivery import Claim, apply_sink, digest


class Rejected(Exception):
    """The requested transition violates the delivery contract."""


def _claim_row(db: sqlite3.Connection, c: Claim, now: int) -> None:
    row = db.execute("""SELECT payload,digest,status,owner,generation,lease_until
                        FROM outbox WHERE id=?""", (c.op_id,)).fetchone()
    if row is None:
        raise Rejected('unbacked operation')
    payload, d, status, owner, generation, lease_until = row
    if (status != 'pending' or payload != c.payload or d != c.digest
        or digest(c.payload) != c.digest or owner != c.owner
        or generation != c.generation or lease_until <= now):
        raise Rejected('claim not current or bound to outbox')


def dispatch(outbox: sqlite3.Connection, sink: sqlite3.Connection,
             c: Claim, now: int) -> str:
    """Verify a current claim before invoking the independent idempotent sink.

    The remote sink still must deduplicate IDs when leases expire in flight.
    """
    _claim_row(outbox, c, now)
    return apply_sink(sink, c, now)


def ack_verified(outbox: sqlite3.Connection, sink: sqlite3.Connection,
                 c: Claim, now: int) -> bool:
    """ACK only a current claim whose destination receipt/effect is durable.

    Assumes a trustworthy sink readback and atomic receipt/effect transaction.
    """
    outbox.execute('BEGIN IMMEDIATE')
    try:
        _claim_row(outbox, c, now)
        receipt = sink.execute('SELECT digest FROM receipts WHERE id=?',
                               (c.op_id,)).fetchone()
        effect = sink.execute('SELECT COUNT(*) FROM effects WHERE op_id=? AND digest=?',
                              (c.op_id, c.digest)).fetchone()[0]
        if receipt != (c.digest,) or effect != 1:
            raise Rejected('no matching durable sink effect')
        changed = outbox.execute("""UPDATE outbox SET status='done',owner=NULL,lease_until=0
                  WHERE id=? AND status='pending' AND owner=? AND generation=?
                  AND lease_until > ?""", (c.op_id,c.owner,c.generation,now)).rowcount
        if changed != 1:
            raise Rejected('lost lease before ack')
        outbox.execute('COMMIT')
        return True
    except BaseException:
        outbox.execute('ROLLBACK')
        raise

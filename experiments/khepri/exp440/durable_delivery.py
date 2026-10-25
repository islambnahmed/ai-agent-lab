"""Exp440: local crash-recovery outbox + idempotent sink simulator.

No network calls. The authorized action's prepared bytes are represented by
an immutable digest supplied by a trusted caller; this module does not validate
real GitHub/Notion/Drive scopes or implement exp439's adapter.
"""
from __future__ import annotations
import hashlib
import sqlite3
from dataclasses import dataclass


def connect(path: str) -> sqlite3.Connection:
    db = sqlite3.connect(path, isolation_level=None, timeout=5)
    db.execute('PRAGMA busy_timeout=5000')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA foreign_keys=ON')
    db.execute("""CREATE TABLE IF NOT EXISTS outbox (
        id TEXT PRIMARY KEY, digest TEXT NOT NULL, payload BLOB NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('pending','done')),
        owner TEXT, lease_until INTEGER NOT NULL DEFAULT 0,
        generation INTEGER NOT NULL DEFAULT 0)""")
    db.execute("""CREATE TABLE IF NOT EXISTS receipts (
        id TEXT PRIMARY KEY, digest TEXT NOT NULL, created_at INTEGER NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS effects (
        id INTEGER PRIMARY KEY AUTOINCREMENT, op_id TEXT NOT NULL,
        digest TEXT NOT NULL, payload BLOB NOT NULL)""")
    return db


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def enqueue(db: sqlite3.Connection, op_id: str, payload: bytes) -> None:
    """Enqueue a prepared wire action. ID reuse with different bytes is invalid."""
    if not isinstance(payload, bytes) or not isinstance(op_id, str) or not op_id:
        raise ValueError('invalid action')
    d = digest(payload)
    db.execute('BEGIN IMMEDIATE')
    try:
        row = db.execute('SELECT digest,payload FROM outbox WHERE id=?', (op_id,)).fetchone()
        if row is None:
            db.execute('INSERT INTO outbox(id,digest,payload,status) VALUES (?,?,?,?)',
                       (op_id, d, payload, 'pending'))
        elif row != (d, payload):
            raise ValueError('operation id reused with different payload')
        db.execute('COMMIT')
    except BaseException:
        db.execute('ROLLBACK')
        raise


@dataclass(frozen=True)
class Claim:
    op_id: str
    payload: bytes
    digest: str
    owner: str
    generation: int


def claim(db: sqlite3.Connection, owner: str, now: int, lease: int = 10) -> Claim | None:
    if not owner or lease <= 0:
        raise ValueError('invalid lease')
    db.execute('BEGIN IMMEDIATE')
    try:
        row = db.execute("""SELECT id,payload,digest,generation FROM outbox
            WHERE status='pending' AND lease_until <= ? ORDER BY id LIMIT 1""",
                         (now,)).fetchone()
        if row is None:
            db.execute('COMMIT')
            return None
        op_id, payload, d, gen = row
        gen += 1
        db.execute("""UPDATE outbox SET owner=?, lease_until=?, generation=?
                      WHERE id=?""", (owner, now + lease, gen, op_id))
        db.execute('COMMIT')
        return Claim(op_id, payload, d, owner, gen)
    except BaseException:
        db.execute('ROLLBACK')
        raise


def apply_sink(db: sqlite3.Connection, c: Claim, now: int) -> str:
    """Simulate remote sink transaction: receipt and effect commit atomically.

    A separate durable sink must provide equivalent atomicity; using one SQLite
    file here is a model of that contract, not a distributed transaction.
    """
    if digest(c.payload) != c.digest:
        raise ValueError('tampered claim')
    db.execute('BEGIN IMMEDIATE')
    try:
        prior = db.execute('SELECT digest FROM receipts WHERE id=?', (c.op_id,)).fetchone()
        if prior is not None:
            if prior[0] != c.digest:
                raise ValueError('same id, different digest')
            outcome = 'duplicate'
        else:
            db.execute('INSERT INTO receipts(id,digest,created_at) VALUES (?,?,?)',
                       (c.op_id, c.digest, now))
            db.execute('INSERT INTO effects(op_id,digest,payload) VALUES (?,?,?)',
                       (c.op_id, c.digest, c.payload))
            outcome = 'applied'
        db.execute('COMMIT')
        return outcome
    except BaseException:
        db.execute('ROLLBACK')
        raise


def ack(db: sqlite3.Connection, c: Claim) -> bool:
    """Fence stale workers; a sink effect may still have happened before failed ack."""
    cur = db.execute("""UPDATE outbox SET status='done',owner=NULL,lease_until=0
        WHERE id=? AND status='pending' AND owner=? AND generation=?""",
        (c.op_id, c.owner, c.generation))
    return cur.rowcount == 1


def purge_receipts(db: sqlite3.Connection, cutoff: int) -> int:
    """Deliberately dangerous TTL simulation for a counterexample."""
    return db.execute('DELETE FROM receipts WHERE created_at < ?', (cutoff,)).rowcount


def effect_count(db: sqlite3.Connection, op_id: str | None = None) -> int:
    if op_id is None:
        return db.execute('SELECT count(*) FROM effects').fetchone()[0]
    return db.execute('SELECT count(*) FROM effects WHERE op_id=?', (op_id,)).fetchone()[0]


def pending_count(db: sqlite3.Connection) -> int:
    return db.execute("SELECT count(*) FROM outbox WHERE status='pending'").fetchone()[0]


def deliver_once(db: sqlite3.Connection, owner: str, now: int,
                 crash_at: str | None = None) -> str:
    """One deterministic dispatch step, with an injected process-crash point."""
    c = claim(db, owner, now)
    if c is None:
        return 'idle'
    if crash_at == 'after_claim':
        return 'crashed_after_claim'
    outcome = apply_sink(db, c, now)
    if crash_at == 'after_effect':
        return 'crashed_after_effect'
    if not ack(db, c):
        return 'stale_ack'
    return outcome

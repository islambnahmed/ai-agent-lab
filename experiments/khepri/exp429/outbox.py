"""Research-only local durable outbox and SQLite idempotent sink.

Two separate SQLite databases model the lack of a distributed transaction.
No external network or third-party services are contacted.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from contextlib import contextmanager


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False)


def event_key(scope, job_id):
    if not all(type(x) is str and x for x in (scope, job_id)):
        raise ValueError('scope and job_id must be nonempty strings')
    return canonical([scope, job_id])  # unambiguous even if identifiers contain ':'


def digest(kind, payload):
    if type(kind) is not str or not kind or type(payload) is not dict:
        raise ValueError('invalid kind or payload')
    return hashlib.sha256(canonical([kind, payload]).encode()).hexdigest()


@contextmanager
def connect(path):
    con = sqlite3.connect(str(path), timeout=10)
    try:
        con.execute('PRAGMA busy_timeout=10000')
        with con:
            yield con
    finally:
        con.close()


class Outbox:
    def __init__(self, path):
        self.path = str(path)
        with connect(self.path) as con:
            con.execute('CREATE TABLE IF NOT EXISTS jobs ('
                        "key TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL, "
                        "fingerprint TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('pending','done')), "
                        "attempts INTEGER NOT NULL DEFAULT 0)")

    def enqueue(self, scope, job_id, kind, payload):
        key = event_key(scope, job_id)
        fingerprint = digest(kind, payload)
        serialized = canonical(payload)
        with connect(self.path) as con:
            con.execute('BEGIN IMMEDIATE')
            existing = con.execute('SELECT fingerprint FROM jobs WHERE key=?', (key,)).fetchone()
            if existing:
                if existing[0] != fingerprint:
                    raise ValueError('conflicting job identity')
                return False
            con.execute('INSERT INTO jobs(key,kind,payload,fingerprint,state) VALUES(?,?,?,?,?)',
                        (key, kind, serialized, fingerprint, 'pending'))
        return True

    def status(self, scope, job_id):
        key = event_key(scope, job_id)
        with connect(self.path) as con:
            row = con.execute('SELECT state,attempts FROM jobs WHERE key=?', (key,)).fetchone()
        return tuple(row) if row else None

    def deliver(self, scope, job_id, sink, *, crash_at=None):
        if crash_at not in (None, 'before_sink', 'after_sink', 'after_ack'):
            raise ValueError('invalid crash point')
        key = event_key(scope, job_id)
        with connect(self.path) as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT kind,payload,state FROM jobs WHERE key=?', (key,)).fetchone()
            if row is None:
                raise KeyError(key)
            if row[2] == 'done':
                return 'already_done'
            con.execute('UPDATE jobs SET attempts=attempts+1 WHERE key=?', (key,))
        if crash_at == 'before_sink':
            raise SimulatedCrash('before_sink')
        outcome = sink.apply(key, row[0], json.loads(row[1]))
        if crash_at == 'after_sink':
            raise SimulatedCrash('after_sink')
        with connect(self.path) as con:
            con.execute('BEGIN IMMEDIATE')
            con.execute("UPDATE jobs SET state='done' WHERE key=?", (key,))
        if crash_at == 'after_ack':
            raise SimulatedCrash('after_ack')
        return outcome


class SimulatedCrash(Exception):
    pass


class IdempotentSink:
    """Effect + receipt are atomically committed in the same sink DB."""
    def __init__(self, path):
        self.path = str(path)
        with connect(self.path) as con:
            con.execute('CREATE TABLE IF NOT EXISTS receipts (key TEXT PRIMARY KEY, fingerprint TEXT NOT NULL)')
            con.execute('CREATE TABLE IF NOT EXISTS effects (seq INTEGER PRIMARY KEY, key TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL)')

    def apply(self, key, kind, payload, *, crash_at=None):
        if crash_at not in (None, 'inside_sink_tx'):
            raise ValueError('invalid sink crash point')
        fingerprint = digest(kind, payload)
        with connect(self.path) as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT fingerprint FROM receipts WHERE key=?', (key,)).fetchone()
            if row:
                if row[0] != fingerprint:
                    raise ValueError('idempotency-key reuse with different payload')
                return 'replayed'
            con.execute('INSERT INTO effects(key,kind,payload) VALUES(?,?,?)', (key, kind, canonical(payload)))
            if crash_at == 'inside_sink_tx':
                raise SimulatedCrash('inside_sink_tx')
            con.execute('INSERT INTO receipts(key,fingerprint) VALUES(?,?)', (key, fingerprint))
        return 'applied'

    def count(self):
        with connect(self.path) as con:
            return con.execute('SELECT COUNT(*) FROM effects').fetchone()[0]

    def count_for(self, key):
        with connect(self.path) as con:
            return con.execute('SELECT COUNT(*) FROM effects WHERE key=?', (key,)).fetchone()[0]


class NonIdempotentSink(IdempotentSink):
    """Negative control: the same downstream operation is repeated on retry."""
    def apply(self, key, kind, payload):
        digest(kind, payload)
        with connect(self.path) as con:
            con.execute('INSERT INTO effects(key,kind,payload) VALUES(?,?,?)', (key, kind, canonical(payload)))
        return 'applied'


class SplitCommitSink(IdempotentSink):
    """Negative control: commits the effect before the receipt; not atomic."""
    def apply(self, key, kind, payload, *, crash_after_effect=False):
        fingerprint = digest(kind, payload)
        with connect(self.path) as con:
            if con.execute('SELECT 1 FROM receipts WHERE key=?', (key,)).fetchone():
                return 'replayed'
            con.execute('INSERT INTO effects(key,kind,payload) VALUES(?,?,?)', (key, kind, canonical(payload)))
        if crash_after_effect:
            raise SimulatedCrash('sink_effect_committed_without_receipt')
        with connect(self.path) as con:
            con.execute('INSERT INTO receipts(key,fingerprint) VALUES(?,?)', (key, fingerprint))
        return 'applied'

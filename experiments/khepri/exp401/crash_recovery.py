"""Crash-boundary idempotency experiment; isolated local SQLite only.

This is a model of downstream delivery, not an integration with a real API.
The mock destination commits separately from the local reservation ledger.
"""
import hashlib
import json
import sqlite3
from pathlib import Path

from sqlite_ledger import connect, mark_complete, reserve

OPS = {'gold.receipt.issue', 'seo.page.publish'}
CUTS = ('before_effect', 'after_effect', 'after_complete', 'none')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':'), allow_nan=False).encode('utf8')).hexdigest()


def scope_key(scope):
    required = ('tenantId', 'operation', 'resourceId', 'intentId')
    if not isinstance(scope, dict) or set(scope) != set(required):
        raise ValueError('Scope must have exactly four fields')
    if scope['operation'] not in OPS:
        raise ValueError('Unknown operation')
    for name in required:
        value = scope[name]
        if not isinstance(value, str) or not (1 <= len(value) <= 180) or value.strip() != value or any(ord(c) < 32 for c in value):
            raise ValueError('Invalid scope field: ' + name)
    return digest({'v': 1, **scope})


class SimulatedCrash(RuntimeError):
    pass


class Destination:
    def __init__(self, path):
        self.db = sqlite3.connect(str(Path(path)), isolation_level=None)
        self.db.execute('CREATE TABLE IF NOT EXISTS effects (seq INTEGER PRIMARY KEY, key TEXT NOT NULL, content TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS keyed (key TEXT PRIMARY KEY, content TEXT NOT NULL)')

    def deliver(self, key, content, keyed):
        # Destination commits independently; no transaction spans this and the local ledger.
        if keyed:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                row = self.db.execute('SELECT content FROM keyed WHERE key=?', (key,)).fetchone()
                if row and row[0] != content:
                    raise ValueError('Destination intent-content conflict')
                if not row:
                    self.db.execute('INSERT INTO keyed(key,content) VALUES(?,?)', (key, content))
                    self.db.execute('INSERT INTO effects(key,content) VALUES(?,?)', (key, content))
                self.db.execute('COMMIT')
            except BaseException:
                self.db.execute('ROLLBACK')
                raise
        else:
            self.db.execute('INSERT INTO effects(key,content) VALUES(?,?)', (key, content))

    def count(self):
        return self.db.execute('SELECT count(*) FROM effects').fetchone()[0]

    def close(self):
        self.db.close()


def attempt(ledger_path, destination_path, scope, payload, mode, cut='none'):
    """mode: replay (unsafe), freeze (no ambiguous retry), keyed (downstream atomic idempotency)."""
    if mode not in ('replay', 'freeze', 'keyed') or cut not in CUTS:
        raise ValueError('Invalid mode or cut')
    key, content = scope_key(scope), digest(payload)
    ledger = connect(ledger_path)
    dest = Destination(destination_path)
    try:
        kind, status = reserve(ledger, key, content)
        if kind == 'conflict':
            raise ValueError('Local intent-content conflict')
        if status == 'complete':
            return 'already_complete'
        if mode == 'freeze' and kind == 'retry':
            return 'ambiguous_stopped'
        if cut == 'before_effect':
            raise SimulatedCrash(cut)
        dest.deliver(key, content, keyed=(mode == 'keyed'))
        if cut == 'after_effect':
            raise SimulatedCrash(cut)
        mark_complete(ledger, key)
        if cut == 'after_complete':
            raise SimulatedCrash(cut)
        return 'complete'
    finally:
        dest.close()
        ledger.close()


def run_sequence(root, scope, payload, mode, cuts):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    lp, dp = root/'ledger.db', root/'destination.db'
    statuses = []
    for cut in (*cuts, 'none'):
        try:
            statuses.append(attempt(lp, dp, scope, payload, mode, cut))
        except SimulatedCrash:
            statuses.append('crash:' + cut)
    dest = Destination(dp)
    try:
        count = dest.count()
    finally:
        dest.close()
    ledger = connect(lp)
    try:
        key = scope_key(scope)
        status = ledger.execute('SELECT status FROM intents WHERE key=?', (key,)).fetchone()[0]
    finally:
        ledger.close()
    return {'effects': count, 'ledger': status, 'attempts': statuses}

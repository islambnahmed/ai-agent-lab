"""Synthetic, transactional approval/state binding demonstration (stdlib SQLite).

This is NOT an authentication mechanism or a remote GitHub writer.
Each approval ID is a local test identifier, not a secret credential.
"""
from __future__ import annotations
import hashlib
from contextlib import contextmanager
import sqlite3
from pathlib import Path


def digest(payload: bytes) -> str:
    if type(payload) is not bytes:
        raise TypeError('payload must be exact bytes')
    return hashlib.sha256(payload).hexdigest()


class ApprovalDB:
    def __init__(self, db_path: str | Path, enforce_triggers: bool = True):
        self.db_path = str(db_path)
        with self._connect() as con:
            con.execute('BEGIN IMMEDIATE')
            con.execute('''CREATE TABLE IF NOT EXISTS heads (
                path TEXT PRIMARY KEY, revision INTEGER NOT NULL CHECK(revision >= 1),
                present INTEGER NOT NULL CHECK(present IN (0,1)), content BLOB)''')
            con.execute('''CREATE TABLE IF NOT EXISTS approvals (
                approval_id TEXT PRIMARY KEY, path TEXT NOT NULL,
                expected_revision INTEGER NOT NULL,
                payload_digest TEXT NOT NULL,
                consumed INTEGER NOT NULL DEFAULT 0 CHECK(consumed IN (0,1)))''')
            if enforce_triggers:
                con.execute("""CREATE TRIGGER IF NOT EXISTS heads_bump_unversioned
                    AFTER UPDATE OF content,present ON heads
                    WHEN NEW.revision = OLD.revision
                    BEGIN UPDATE heads SET revision=revision+1 WHERE path=NEW.path; END""")
                con.execute("""CREATE TRIGGER IF NOT EXISTS heads_no_physical_delete
                    BEFORE DELETE ON heads
                    BEGIN SELECT RAISE(ABORT,'physical deletion forbidden; use tombstone'); END""")
                con.execute("""CREATE TRIGGER IF NOT EXISTS heads_no_revision_regression
                    BEFORE UPDATE OF revision ON heads
                    WHEN NEW.revision <= OLD.revision
                    BEGIN SELECT RAISE(ABORT,'revision must increase'); END""")
            con.commit()

    @contextmanager
    def _connect(self):
        con = sqlite3.connect(self.db_path, timeout=15, isolation_level=None)
        try:
            con.execute('PRAGMA busy_timeout=15000')
            con.execute('PRAGMA synchronous=FULL')
            yield con
        finally:
            con.close()

    @staticmethod
    def _revision(con, path: str) -> int:
        row = con.execute('SELECT revision FROM heads WHERE path=?', (path,)).fetchone()
        return row[0] if row else 0

    def snapshot(self, path: str):
        with self._connect() as con:
            row = con.execute('SELECT revision,present,content FROM heads WHERE path=?', (path,)).fetchone()
            return row if row else (0, 0, None)

    def external_write(self, path: str, payload: bytes):
        digest(payload)
        with self._connect() as con:
            con.execute('BEGIN IMMEDIATE')
            con.execute('''INSERT INTO heads(path,revision,present,content) VALUES (?,1,1,?)
                ON CONFLICT(path) DO UPDATE SET revision=revision+1,present=1,content=excluded.content''',
                (path, payload))
            con.commit()

    def external_delete(self, path: str):
        with self._connect() as con:
            con.execute('BEGIN IMMEDIATE')
            con.execute('''INSERT INTO heads(path,revision,present,content) VALUES (?,1,0,NULL)
                ON CONFLICT(path) DO UPDATE SET revision=revision+1,present=0,content=NULL''', (path,))
            con.commit()

    def issue(self, approval_id: str, path: str, payload: bytes):
        """Issuance is a simulation of a *previously authorized* action."""
        payload_hash = digest(payload)
        if type(approval_id) is not str or not approval_id:
            raise ValueError('nonempty approval ID required')
        if type(path) is not str or not path:
            raise ValueError('nonempty path required')
        with self._connect() as con:
            con.execute('BEGIN IMMEDIATE')
            revision = self._revision(con, path)
            con.execute('''INSERT INTO approvals(approval_id,path,expected_revision,payload_digest)
                VALUES (?,?,?,?)''', (approval_id,path,revision,payload_hash))
            con.commit()
            return revision

    def redeem(self, approval_id: str, path: str, payload: bytes) -> str:
        """All state checks and the side effect share one write transaction."""
        payload_hash = digest(payload)
        with self._connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('''SELECT path,expected_revision,payload_digest,consumed
                FROM approvals WHERE approval_id=?''', (approval_id,)).fetchone()
            if row is None or row[3] != 0:
                con.rollback()
                return 'invalid_or_consumed'
            if row[0] != path or row[2] != payload_hash:
                con.rollback()
                return 'plan_mismatch'
            # One attempt consumes a valid receipt, even if the state became stale.
            con.execute('UPDATE approvals SET consumed=1 WHERE approval_id=?', (approval_id,))
            current = self._revision(con, path)
            if current != row[1]:
                con.commit()
                return 'stale'
            if current == 0:
                con.execute('INSERT INTO heads(path,revision,present,content) VALUES (?,1,1,?)', (path,payload))
            else:
                result = con.execute('''UPDATE heads SET revision=revision+1,present=1,content=?
                    WHERE path=? AND revision=?''', (payload,path,current))
                if result.rowcount != 1:
                    con.rollback()
                    return 'conflict'
            con.commit()
            return 'ok'

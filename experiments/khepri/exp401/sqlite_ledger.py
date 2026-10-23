"""Durable local reference for scoped idempotency reservations.

No external side effects are performed. A reserved record after a crash remains
ambiguous; it MUST NOT be blindly replayed. Not a distributed exactly-once system.
"""
import re
import sqlite3
from pathlib import Path

HEX = re.compile(r"^[0-9a-f]{64}$")


def connect(path):
    con = sqlite3.connect(str(Path(path)), timeout=10, isolation_level=None)
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("CREATE TABLE IF NOT EXISTS intents (key TEXT PRIMARY KEY, content TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('reserved','complete')))")
    return con


def reserve(con, key, content):
    if not isinstance(key, str) or not HEX.fullmatch(key) or not isinstance(content, str) or not HEX.fullmatch(content):
        raise ValueError("SHA-256 hex digests required")
    con.execute("BEGIN IMMEDIATE")
    try:
        row = con.execute("SELECT content, status FROM intents WHERE key=?", (key,)).fetchone()
        if row is None:
            con.execute("INSERT INTO intents(key,content,status) VALUES(?,?,'reserved')", (key, content))
            result = ("new", "reserved")
        elif row[0] != content:
            result = ("conflict", row[1])
        else:
            result = ("retry", row[1])
        con.execute("COMMIT")
        return result
    except BaseException:
        con.execute("ROLLBACK")
        raise


def mark_complete(con, key):
    con.execute("UPDATE intents SET status='complete' WHERE key=?", (key,))
    if con.execute("SELECT changes()").fetchone()[0] != 1:
        raise KeyError("Reservation missing")

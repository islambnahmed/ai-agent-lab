"""Local synthetic retention models; effects and receipts share SQLite transactions."""
import hashlib
import json
import sqlite3
from typing import Optional

def digest(payload):
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

class TimedReceiptSink:
    """Negative control: TTL receipts allow duplicates after expiry."""
    def __init__(self, ttl: Optional[int]):
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.ttl = ttl
        self.db.executescript("""
            CREATE TABLE receipts(stream TEXT, seq INTEGER, digest TEXT, expires INTEGER,
                                  PRIMARY KEY(stream,seq));
            CREATE TABLE effects(id INTEGER PRIMARY KEY, stream TEXT, seq INTEGER);
        """)

    def deliver(self, stream, seq, payload, now):
        h = digest(payload)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            if self.ttl is not None:
                self.db.execute("DELETE FROM receipts WHERE expires <= ?", (now,))
            row = self.db.execute("SELECT digest FROM receipts WHERE stream=? AND seq=?", (stream,seq)).fetchone()
            if row:
                if row[0] != h:
                    raise ValueError("conflicting payload for key")
                outcome = "replayed"
            else:
                self.db.execute("INSERT INTO effects(stream,seq) VALUES (?,?)", (stream,seq))
                expiry = now + self.ttl if self.ttl is not None else -1
                self.db.execute("INSERT INTO receipts VALUES (?,?,?,?)", (stream,seq,h,expiry))
                outcome = "applied"
            self.db.execute("COMMIT")
            return outcome
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def close(self):
        self.db.close()

    def effect_count(self):
        return self.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0]

    def receipt_count(self):
        return self.db.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]

class ContiguousWatermarkSink:
    """Registered monotonic stream intents; atomically apply and compact done prefix.

    Unknown/stale sequences fail closed. A pruned payload/result cannot be verified.
    """
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS streams(stream TEXT PRIMARY KEY, issued INTEGER NOT NULL,
                                 watermark INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS intents(stream TEXT, seq INTEGER, digest TEXT NOT NULL,
                                 status TEXT NOT NULL CHECK(status IN ('pending','done','cancelled')),
                                 PRIMARY KEY(stream,seq));
            CREATE TABLE IF NOT EXISTS effects(id INTEGER PRIMARY KEY, stream TEXT, seq INTEGER);
        """)

    def issue(self, stream, payload):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("INSERT OR IGNORE INTO streams VALUES (?,0,0)", (stream,))
            seq = self.db.execute("SELECT issued FROM streams WHERE stream=?", (stream,)).fetchone()[0]+1
            self.db.execute("UPDATE streams SET issued=? WHERE stream=?", (seq,stream))
            self.db.execute("INSERT INTO intents VALUES (?,?,?,'pending')", (stream,seq,digest(payload)))
            self.db.execute("COMMIT")
            return seq
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _compact(self, stream):
        watermark = self.db.execute("SELECT watermark FROM streams WHERE stream=?", (stream,)).fetchone()[0]
        while True:
            row = self.db.execute("SELECT status FROM intents WHERE stream=? AND seq=?", (stream,watermark+1)).fetchone()
            if row is None or row[0] not in ("done", "cancelled"):
                break
            watermark += 1
            self.db.execute("DELETE FROM intents WHERE stream=? AND seq=?", (stream,watermark))
        self.db.execute("UPDATE streams SET watermark=? WHERE stream=?", (watermark,stream))

    def deliver(self, stream, seq, payload):
        h = digest(payload)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT watermark FROM streams WHERE stream=?", (stream,)).fetchone()
            if row is None:
                raise ValueError("unknown stream")
            if seq <= row[0]:
                outcome = "stale_rejected"  # NOT a success acknowledgement.
            else:
                intent = self.db.execute("SELECT digest,status FROM intents WHERE stream=? AND seq=?", (stream,seq)).fetchone()
                if intent is None:
                    raise ValueError("unregistered sequence")
                if intent[0] != h:
                    raise ValueError("conflicting payload")
                if intent[1] == "done":
                    outcome = "replayed"
                elif intent[1] == "cancelled":
                    outcome = "cancelled_rejected"
                else:
                    self.db.execute("INSERT INTO effects(stream,seq) VALUES (?,?)", (stream,seq))
                    self.db.execute("UPDATE intents SET status='done' WHERE stream=? AND seq=?", (stream,seq))
                    self._compact(stream)
                    outcome = "applied"
            self.db.execute("COMMIT")
            return outcome
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def cancel(self, stream, seq):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT status FROM intents WHERE stream=? AND seq=?", (stream,seq)).fetchone()
            if row is None or row[0] != "pending":
                raise ValueError("cannot cancel missing/finished intent")
            self.db.execute("UPDATE intents SET status='cancelled' WHERE stream=? AND seq=?", (stream,seq))
            self._compact(stream)
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def close(self):
        self.db.close()

    def effect_count(self):
        return self.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0]

    def receipt_count(self):
        return self.db.execute("SELECT COUNT(*) FROM intents").fetchone()[0]

    def watermark(self, stream):
        return self.db.execute("SELECT watermark FROM streams WHERE stream=?", (stream,)).fetchone()[0]

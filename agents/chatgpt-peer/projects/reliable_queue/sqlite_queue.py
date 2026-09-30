"""Transactional SQLite queue backend for concurrent local workers."""
from __future__ import annotations
import json,sqlite3,time,uuid

class SQLiteQueue:
    def __init__(self,path):
        self.path=str(path); self._init()

    def _db(self):
        db=sqlite3.connect(self.path,timeout=5,isolation_level=None)
        db.row_factory=sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        return db

    def _init(self):
        with self._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS tasks(
              id TEXT PRIMARY KEY,payload TEXT NOT NULL,status TEXT NOT NULL,
              attempts INTEGER NOT NULL,max_attempts INTEGER NOT NULL,
              available_at REAL NOT NULL,lease_until REAL,lease_token TEXT,last_error TEXT)""")

    def add(self,payload,max_attempts=3):
        if max_attempts<1:raise ValueError("max_attempts must be >=1")
        tid=uuid.uuid4().hex
        with self._db() as db:
            db.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?)",
              (tid,json.dumps(payload,ensure_ascii=False),"pending",0,max_attempts,0.0,None,None,None))
        return tid

    def claim(self,now=None,visibility_timeout=30):
        now=time.time() if now is None else float(now); token=uuid.uuid4().hex
        db=self._db()
        try:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""UPDATE tasks SET
              status=CASE WHEN attempts>=max_attempts THEN 'dead' ELSE 'pending' END,
              available_at=CASE WHEN attempts>=max_attempts THEN available_at ELSE ? END,
              lease_until=NULL,lease_token=NULL
              WHERE status='running' AND lease_until<=?""",(now,now))
            row=db.execute("""SELECT * FROM tasks WHERE status='pending' AND available_at<=?
              ORDER BY rowid LIMIT 1""",(now,)).fetchone()
            if row is None: db.commit(); return None
            lease=now+max(.001,float(visibility_timeout))
            cur=db.execute("""UPDATE tasks SET status='running',attempts=attempts+1,
              lease_until=?,lease_token=? WHERE id=? AND status='pending'""",(lease,token,row["id"]))
            if cur.rowcount!=1: db.rollback(); return None
            out=db.execute("SELECT * FROM tasks WHERE id=?",(row["id"],)).fetchone()
            db.commit(); return self._decode(out)
        except: db.rollback(); raise
        finally: db.close()

    def complete(self,task_id,lease_token):
        with self._db() as db:
            cur=db.execute("""UPDATE tasks SET status='done',lease_until=NULL,lease_token=NULL
              WHERE id=? AND status='running' AND lease_token=?""",(task_id,lease_token))
            if cur.rowcount!=1:raise ValueError("stale or invalid lease token")

    def fail(self,task_id,lease_token,error,retry_delay=0,now=None):
        now=time.time() if now is None else float(now)
        db=self._db()
        try:
            db.execute("BEGIN IMMEDIATE")
            row=db.execute("SELECT * FROM tasks WHERE id=? AND status='running' AND lease_token=?",
                           (task_id,lease_token)).fetchone()
            if row is None:raise ValueError("stale or invalid lease token")
            status="dead" if row["attempts"]>=row["max_attempts"] else "pending"
            db.execute("""UPDATE tasks SET status=?,available_at=?,lease_until=NULL,
              lease_token=NULL,last_error=? WHERE id=?""",
              (status,now+max(0,float(retry_delay)),str(error),task_id))
            db.commit()
        except: db.rollback(); raise
        finally: db.close()

    def snapshot(self):
        with self._db() as db:return [self._decode(r) for r in db.execute("SELECT * FROM tasks ORDER BY rowid")]

    @staticmethod
    def _decode(row):
        d=dict(row); d["payload"]=json.loads(d["payload"]); return d

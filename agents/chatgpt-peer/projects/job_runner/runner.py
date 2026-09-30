"""Small durable local job runner built on reliable_queue.SQLiteQueue."""
from __future__ import annotations
import json,time
from pathlib import Path
import importlib.util

def _load_queue():
    p=Path(__file__).parents[1]/"reliable_queue"/"sqlite_queue.py"
    s=importlib.util.spec_from_file_location("sqlite_queue",p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
_q=_load_queue()

class JobRunner:
    def __init__(self,db_path):
        self.queue=_q.SQLiteQueue(db_path)
        self.handlers={}
        self._init_results()

    def _init_results(self):
        with self.queue._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS job_results(
              task_id TEXT PRIMARY KEY,status TEXT NOT NULL,result_json TEXT,error TEXT,
              updated_at REAL NOT NULL)""")

    def _record(self,task_id,status,result=None,error=None,now=None):
        ts=time.time() if now is None else float(now)
        result_json=None if result is None else json.dumps(result,ensure_ascii=False)
        with self.queue._db() as db:
            db.execute("""INSERT INTO job_results(task_id,status,result_json,error,updated_at)
              VALUES(?,?,?,?,?) ON CONFLICT(task_id) DO UPDATE SET
              status=excluded.status,result_json=excluded.result_json,
              error=excluded.error,updated_at=excluded.updated_at""",
              (task_id,status,result_json,error,ts))

    def result(self,task_id):
        with self.queue._db() as db:
            row=db.execute("SELECT * FROM job_results WHERE task_id=?",(task_id,)).fetchone()
            task=db.execute("SELECT status,attempts,max_attempts,last_error FROM tasks WHERE id=?",(task_id,)).fetchone()
        if row is None:return None
        d=dict(row); raw=d.pop("result_json")
        d["result"]=None if raw is None else json.loads(raw)
        if task is not None:
            d["queue_status"]=task["status"]; d["attempts"]=task["attempts"]
            d["max_attempts"]=task["max_attempts"]; d["last_error"]=task["last_error"]
        return d

    def _record_after_failure(self,task_id,error,now=None):
        with self.queue._db() as db:
            row=db.execute("SELECT status FROM tasks WHERE id=?",(task_id,)).fetchone()
        terminal=row is not None and row["status"]=="dead"
        self._record(task_id,"dead" if terminal else "retrying",error=error,now=now)

    def register(self,name,fn):
        if not name or not callable(fn):raise ValueError("invalid handler")
        self.handlers[name]=fn

    def submit(self,name,args=None,dedupe_key=None,available_at=0,max_attempts=3):
        payload={"handler":name,"args":args or {}}
        tid=self.queue.add(payload,max_attempts=max_attempts,dedupe_key=dedupe_key,available_at=available_at)
        if self.result(tid) is None:self._record(tid,"queued")
        return tid

    def work_once(self,now=None,visibility_timeout=30):
        task=self.queue.claim(now=now,visibility_timeout=visibility_timeout)
        if task is None:return None
        payload=task["payload"]; name=payload.get("handler")
        fn=self.handlers.get(name)
        if fn is None:
            self.queue.fail(task["id"],task["lease_token"],f"unknown handler: {name}",now=now)
            self._record_after_failure(task["id"],"unknown handler",now=now)
            return {"task_id":task["id"],"status":"failed","error":"unknown handler"}
        try:
            result=fn(**payload.get("args",{}))
            # Results must be JSON serializable before task completion.
            json.dumps(result,ensure_ascii=False)
            self.queue.complete(task["id"],task["lease_token"])
            self._record(task["id"],"done",result=result,now=now)
            return {"task_id":task["id"],"status":"done","result":result}
        except Exception as e:
            # A handler may run longer than its lease. If another worker has
            # already recovered the task, this worker must not mutate the new claim.
            try:
                self.queue.fail(task["id"],task["lease_token"],f"{type(e).__name__}: {e}",now=now)
            except ValueError:
                return {"task_id":task["id"],"status":"stale","error":str(e)}
            self._record_after_failure(task["id"],str(e),now=now)
            return {"task_id":task["id"],"status":"failed","error":str(e)}

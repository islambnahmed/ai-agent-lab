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

    def register(self,name,fn):
        if not name or not callable(fn):raise ValueError("invalid handler")
        self.handlers[name]=fn

    def submit(self,name,args=None,dedupe_key=None,available_at=0,max_attempts=3):
        payload={"handler":name,"args":args or {}}
        return self.queue.add(payload,max_attempts=max_attempts,dedupe_key=dedupe_key,available_at=available_at)

    def work_once(self,now=None,visibility_timeout=30):
        task=self.queue.claim(now=now,visibility_timeout=visibility_timeout)
        if task is None:return None
        payload=task["payload"]; name=payload.get("handler")
        fn=self.handlers.get(name)
        if fn is None:
            self.queue.fail(task["id"],task["lease_token"],f"unknown handler: {name}",now=now)
            return {"task_id":task["id"],"status":"failed","error":"unknown handler"}
        try:
            result=fn(**payload.get("args",{}))
            # Results must be JSON serializable before task completion.
            json.dumps(result,ensure_ascii=False)
            self.queue.complete(task["id"],task["lease_token"])
            return {"task_id":task["id"],"status":"done","result":result}
        except Exception as e:
            self.queue.fail(task["id"],task["lease_token"],f"{type(e).__name__}: {e}",now=now)
            return {"task_id":task["id"],"status":"failed","error":str(e)}

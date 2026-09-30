"""Small persistent task queue using only the Python standard library."""
from __future__ import annotations
import json, os, tempfile, time, uuid
from pathlib import Path

class Queue:
    def __init__(self,path):
        self.path=Path(path)
        self.state={"version":1,"tasks":[]}
        if self.path.exists(): self._load()

    def _load(self):
        raw=json.loads(self.path.read_text(encoding="utf-8"))
        if raw.get("version")!=1 or not isinstance(raw.get("tasks"),list):
            raise ValueError("unsupported/corrupt queue state")
        self.state=raw

    def _save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(dir=self.path.parent,prefix=self.path.name+".",suffix=".tmp")
        try:
            with os.fdopen(fd,"w",encoding="utf-8") as f:
                json.dump(self.state,f,ensure_ascii=False,separators=(",",":"))
                f.flush(); os.fsync(f.fileno())
            os.replace(tmp,self.path)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)

    def add(self,payload,max_attempts=3):
        if max_attempts<1: raise ValueError("max_attempts must be >=1")
        task={"id":uuid.uuid4().hex,"payload":payload,"status":"pending",
              "attempts":0,"max_attempts":max_attempts,"available_at":0.0,
              "lease_until":None,"lease_token":None,"last_error":None}
        self.state["tasks"].append(task); self._save(); return task["id"]

    def claim(self,now=None,visibility_timeout=30):
        now=time.time() if now is None else float(now)
        changed=False
        for t in self.state["tasks"]:
            # Expired leases make abandoned work visible again.
            if t["status"]=="running" and t.get("lease_until") is not None and t["lease_until"]<=now:
                if t["attempts"]>=t["max_attempts"]:
                    t["status"]="dead"; t["lease_until"]=None; t["lease_token"]=None
                else:
                    t["status"]="pending"; t["available_at"]=now; t["lease_until"]=None; t["lease_token"]=None
                changed=True
        for t in self.state["tasks"]:
            if t["status"]=="pending" and t["available_at"]<=now:
                t["status"]="running"; t["attempts"]+=1
                t["lease_until"]=now+max(0.001,float(visibility_timeout)); t["lease_token"]=uuid.uuid4().hex; self._save()
                return dict(t)
        if changed:self._save()
        return None

    def _assert_lease(self,t,lease_token):
        if t["status"]!="running": raise ValueError("task is not running")
        if not lease_token or t.get("lease_token")!=lease_token:
            raise ValueError("stale or invalid lease token")

    def complete(self,task_id,lease_token):
        t=self._get(task_id); self._assert_lease(t,lease_token)
        t["status"]="done"; t["lease_until"]=None; t["lease_token"]=None; self._save()

    def renew(self,task_id,lease_token,visibility_timeout=30,now=None):
        t=self._get(task_id); self._assert_lease(t,lease_token)
        now=time.time() if now is None else float(now)
        if t.get("lease_until") is not None and t["lease_until"]<=now:
            raise ValueError("lease already expired")
        t["lease_until"]=now+max(0.001,float(visibility_timeout)); self._save()
        return t["lease_until"]

    def fail(self,task_id,lease_token,error,retry_delay=0,now=None):
        t=self._get(task_id); self._assert_lease(t,lease_token)
        t["last_error"]=str(error); t["lease_until"]=None; t["lease_token"]=None
        if t["attempts"]>=t["max_attempts"]:
            t["status"]="dead"
        else:
            t["status"]="pending"
            t["available_at"]=(time.time() if now is None else float(now))+max(0,float(retry_delay))
        self._save()

    def _get(self,task_id):
        for t in self.state["tasks"]:
            if t["id"]==task_id:return t
        raise KeyError(task_id)

    def snapshot(self):
        return json.loads(json.dumps(self.state))

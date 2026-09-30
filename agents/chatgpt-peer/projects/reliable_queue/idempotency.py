"""Durable idempotent effect journal for local queue workers.

prepare -> external effect -> commit cannot make an arbitrary external system
exactly-once. This module instead supports effects that can be represented and
committed locally, or external systems that honor the same idempotency key.
"""
from __future__ import annotations
import json,os,tempfile
from pathlib import Path

class EffectJournal:
    def __init__(self,path):
        self.path=Path(path); self.data={"version":1,"effects":{}}
        if self.path.exists(): self.data=json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(dir=self.path.parent,prefix=self.path.name+".",suffix=".tmp")
        try:
            with os.fdopen(fd,"w",encoding="utf-8") as f:
                json.dump(self.data,f,ensure_ascii=False,separators=(",",":")); f.flush(); os.fsync(f.fileno())
            os.replace(tmp,self.path)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)

    def execute_once(self,key,fn):
        if key in self.data["effects"]:
            return self.data["effects"][key]["result"],False
        result=fn()
        self.data["effects"][key]={"result":result}
        self._save()
        return result,True

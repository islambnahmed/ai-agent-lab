from pathlib import Path
import tempfile,sqlite3,importlib.util
p=Path(__file__).with_name("sqlite_queue.py")
s=importlib.util.spec_from_file_location("sq",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 dbp=Path(d)/"old.db"
 db=sqlite3.connect(dbp)
 db.execute("""CREATE TABLE tasks(id TEXT PRIMARY KEY,payload TEXT NOT NULL,status TEXT NOT NULL,
 attempts INTEGER NOT NULL,max_attempts INTEGER NOT NULL,available_at REAL NOT NULL,
 lease_until REAL,lease_token TEXT,last_error TEXT)""")
 db.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?)",("old",'{"x":1}',"pending",0,3,0,None,None,None))
 db.commit();db.close()
 q=m.SQLiteQueue(dbp)
 cols={r["name"] for r in q._db().execute("PRAGMA table_info(tasks)")}
 assert "dedupe_key" in cols
 assert q.snapshot()[0]["id"]=="old"
 assert q.add("new",dedupe_key="k")==q.add("ignored",dedupe_key="k")
print("PASS")

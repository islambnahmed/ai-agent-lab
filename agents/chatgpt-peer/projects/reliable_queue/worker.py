"""Worker helper combining Queue claims with stable task idempotency keys."""
from __future__ import annotations

def process_one(queue,journal,handler,now=None,visibility_timeout=30):
    task=queue.claim(now=now,visibility_timeout=visibility_timeout)
    if task is None:return None
    key="task:"+task["id"]
    try:
        result,fresh=journal.execute_once(key,lambda:handler(task["payload"],key))
        queue.complete(task["id"],task["lease_token"])
        return {"task_id":task["id"],"result":result,"effect_executed":fresh}
    except Exception as e:
        # Failure to record/execute is retried; stale completion is intentionally surfaced.
        try: queue.fail(task["id"],task["lease_token"],str(e),now=now)
        except ValueError: pass
        raise

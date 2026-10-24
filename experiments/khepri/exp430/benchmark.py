"""Deterministic workload; counts are constructed examples, not field rates."""
import json
from retention import TimedReceiptSink, ContiguousWatermarkSink

def run(n=400, late=100, ttl=30, retry_time=100):
    ttl_sink=TimedReceiptSink(ttl=ttl)
    forever=TimedReceiptSink(ttl=None)
    compact=ContiguousWatermarkSink()
    for stream in ("seo", "gold"):
        for i in range(1,n+1):
            payload={"case":stream,"value":i}
            assert compact.issue(stream,payload)==i
            assert ttl_sink.deliver(stream,i,payload,0)=="applied"
            assert forever.deliver(stream,i,payload,0)=="applied"
            assert compact.deliver(stream,i,payload)=="applied"
        for i in range(1,late+1):
            payload={"case":stream,"value":i}
            assert ttl_sink.deliver(stream,i,payload,retry_time)=="applied"
            assert forever.deliver(stream,i,payload,retry_time)=="replayed"
            assert compact.deliver(stream,i,payload)=="stale_rejected"
    result={"parameters":{"streams":2,"intents_per_stream":n,"late_retries_per_stream":late,"ttl":ttl,"retry_time":retry_time},
            "intended_effects":2*n,
            "ttl":{"effects":ttl_sink.effect_count(),"extra_effects":ttl_sink.effect_count()-2*n,"active_receipts":ttl_sink.receipt_count()},
            "permanent":{"effects":forever.effect_count(),"extra_effects":forever.effect_count()-2*n,"active_receipts":forever.receipt_count()},
            "contiguous_watermark":{"effects":compact.effect_count(),"extra_effects":compact.effect_count()-2*n,"active_intents":compact.receipt_count(),"stream_watermarks":{"seo":compact.watermark("seo"),"gold":compact.watermark("gold")}}}
    ttl_sink.close(); forever.close(); compact.close()
    return result

if __name__=="__main__": print(json.dumps(run(),indent=2,sort_keys=True))

"""Deterministic fault-injection benchmark; counts are NOT empirical probabilities."""
import json
import tempfile
from pathlib import Path
from outbox import Outbox, IdempotentSink, NonIdempotentSink, SimulatedCrash

SCENARIOS = {'clean':0, 'before_sink':1, 'after_sink':1, 'two_after_sink':2, 'after_ack':1}


def run(n=200):
    results = {}
    with tempfile.TemporaryDirectory() as root:
        for domain in ('seo', 'gold'):
            domain_result = {}
            for scenario in SCENARIOS:
                counts = {}
                for label, sink_type in [('no_sink_dedupe',NonIdempotentSink),('atomic_sink_dedupe',IdempotentSink)]:
                    base=Path(root)/f'{domain}_{scenario}_{label}'
                    box=Outbox(str(base)+'_box.sqlite')
                    sink=sink_type(str(base)+'_sink.sqlite')
                    for i in range(n):
                        kind,payload = (('lead',{'lead':f'synthetic-{i}','score':i%5}) if domain=='seo'
                                        else ('quote',{'symbol':'XAU','tick':i,'value':1900+i%31}))
                        job=f'{scenario}-{i}'
                        box.enqueue(domain,job,kind,payload)
                        crashes = {'clean':[], 'before_sink':['before_sink'],
                                   'after_sink':['after_sink'], 'two_after_sink':['after_sink','after_sink'],
                                   'after_ack':['after_ack']}[scenario]
                        for crash in crashes:
                            try:
                                box.deliver(domain,job,sink,crash_at=crash)
                            except SimulatedCrash:
                                pass
                        box.deliver(domain,job,sink)
                        assert box.status(domain,job)[0]=='done'
                    counts[label]={'effects':sink.count(), 'expected':n, 'extra':sink.count()-n}
                domain_result[scenario]=counts
            results[domain]=domain_result
    return results


if __name__=='__main__':
    print(json.dumps(run(),indent=2,sort_keys=True))

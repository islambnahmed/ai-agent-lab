"""Seeded synthetic SEO and gold planning benchmark. No external actions."""
import json
from statistics import mean
from source_benchmark import random_instance
from repair import optimize


def run(trials=500):
    output={'seed':432, 'trials_per_domain':trials, 'domains':{}}
    for j,domain in enumerate(('seo','gold')):
        rows=[]
        for i in range(trials):
            p=random_instance(domain,432000+j*100000+i)
            oracle=p.exact()
            base=p.greedy(marginal=True)
            one=optimize(p,max_drop=1)
            seeded=optimize(p,max_drop=1,seeded=True)
            two=optimize(p,max_drop=2,seeded=True)
            rows.append((oracle,base,one,seeded,two))
        names=('oracle','marginal','one_drop','seeded_one_drop','seeded_two_drop')
        output['domains'][domain]={
            name:{'mean_value':round(mean(r[k].value for r in rows),4),
                  'mean_cost':round(mean(r[k].cost for r in rows),4),
                  'oracle_matches':sum(abs(r[k].value-r[0].value)<1e-9 for r in rows),
                  'strictly_beats_marginal':sum(r[k].value>r[1].value+1e-9 for r in rows),
                  'below_marginal':sum(r[k].value+1e-9<r[1].value for r in rows)}
            for k,name in enumerate(names)}
    return output
if __name__=='__main__': print(json.dumps(run(),sort_keys=True,indent=2))

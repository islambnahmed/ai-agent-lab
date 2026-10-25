import json
from ope import SEO,GOLD,run_benchmark

if __name__=='__main__':
    results={'seo':run_benchmark(SEO),'gold':run_benchmark(GOLD)}
    with open('benchmark_results.json','w',encoding='utf-8') as f:
        json.dump(results,f,indent=2,sort_keys=True)
        f.write('\n')
    print(json.dumps(results,indent=2))

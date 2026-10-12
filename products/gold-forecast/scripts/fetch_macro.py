"""Collect official FRED snapshots; receivedAt is the conservative availableAt.
These current vintages must NOT be used as historical point-in-time features.
"""
import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
from pathlib import Path
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
SERIES={'DFII10':'real_yield_10y_pct','DGS10':'nominal_yield_10y_pct','DTWEXBGS':'broad_dollar_index','CPIAUCSL':'us_cpi_index','DFF':'effective_fed_funds_pct'}

def fetch(series,feature):
    # The graph CSV endpoint is a public export, without an API key.
    url=f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}&cosd=2000-01-01'
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'GoldLab/2.0 research'}),timeout=25) as r:
            raw=r.read(5_000_001)
        if len(raw)>5_000_000: raise ValueError('CSV response too large')
        stamp=dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
        rows=[]
        seen=set()
        for row in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
            value=row.get(series)
            if value in (None,'','.'): continue
            day=row.get('observation_date') or row.get('DATE')
            dt.date.fromisoformat(day)
            if day>stamp[:10] or day in seen: raise ValueError('Future or duplicate macro observation')
            numeric=float(value)
            if not math.isfinite(numeric): raise ValueError('Nonfinite macro observation')
            seen.add(day)
            rows.append({'feature':feature,'value':numeric,'observedAt':day+'T00:00:00Z',
                         'availableAt':stamp,'source':'FRED:'+series,'vintage':stamp})
        if not rows: raise ValueError('No parsed observations')
        return rows,{'series':series,'url':url,'sourcePage':'https://fred.stlouisfed.org/series/'+series,
                     'receivedAt':stamp,'rawSha256':hashlib.sha256(raw).hexdigest(),'rows':len(rows),'latest':rows[-1],
                     'status':'fetched','use':'current-vintage research / future origins only'}
    except Exception as e:
        # A failed CSV export is not evidence that a current observation is
        # unavailable. Fall back explicitly to the authoritative series page.
        page=f'https://fred.stlouisfed.org/series/{series}'
        try:
            with urllib.request.urlopen(page,timeout=25) as response:
                raw=response.read(5_000_001)
            text=raw.decode('utf-8')
            match=re.search(r'(\d{4}-\d{2}-\d{2}):\s*<span class="series-meta-observation-value">\s*([-\d.,]+)\s*</span>',text)
            if match:
                day,value=match.groups()
            else:
                # Monthly series display "Aug 2026", not a day label. Their
                # canonical ISO observation date is in PeriodOfTime metadata.
                value_match=re.search(r'<span class="series-meta-observation-value">\s*([-\d.,]+)\s*</span>',text)
                day_match=re.search(r'name="dcterms:PeriodOfTime" content="start:[^;]+; end:(\d{4}-\d{2}-\d{2});"',text)
                if not value_match or not day_match: raise ValueError('FRED current observation markup changed')
                day,value=day_match.group(1),value_match.group(1)
            dt.date.fromisoformat(day)
            stamp=dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
            if day>stamp[:10]: raise ValueError('Future macro observation')
            row={'feature':feature,'value':float(value.replace(',','')),'observedAt':day+'T00:00:00Z',
                 'availableAt':stamp,'source':'FRED:'+series,'vintage':stamp}
            return [row],{'series':series,'sourcePage':page,'receivedAt':stamp,'rawSha256':hashlib.sha256(raw).hexdigest(),
                'rows':1,'latest':row,'status':'fetched_current_observation','historicalExportStatus':'unavailable',
                'historicalExportError':str(e),'use':'future/current context only; NOT historical training'}
        except Exception as fallback:
            return [],{'series':series,'url':url,'status':'unavailable','error':str(e),'fallbackError':str(fallback)}

def main():
    records=[];manifest=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for future in [pool.submit(fetch,s,f) for s,f in SERIES.items()]:
            rows,meta=future.result();records.extend(rows);manifest.append(meta)
    ROOT.joinpath('data').mkdir(exist_ok=True)
    ROOT.joinpath('reports').mkdir(exist_ok=True)
    ROOT.joinpath('data/macro.json').write_text(json.dumps(records,indent=2))
    ROOT.joinpath('reports/macro-sources-20261012.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()

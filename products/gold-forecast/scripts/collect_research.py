"""Public downloads, verified before use. Raw vendor data stays in ignored data/.

HistData M1 bars are bid prices, EST UTC-5 without DST. Daily rows use the last
observed minute close in a completed UTC day; missing minutes/days stay missing.
ALFRED columns are historical snapshots, sampled monthly, NOT release timestamps.
"""
import argparse
import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
from html.parser import HTMLParser
from pathlib import Path
import urllib.parse
import urllib.request
import zipfile
from fetch_macro import SERIES

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'data/source-research'
OFFLINE = False
EST=dt.timezone(dt.timedelta(hours=-5))
MINUTE_STAMP=re.compile(r'^\d{8} \d{6}$')

def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

def download(url, data=None, headers=None):
    if OFFLINE: raise ValueError('No cached response; network disabled for offline rebuild')
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'GoldLab/2.0 research', **(headers or {})})
    with urllib.request.urlopen(req, timeout=55) as response:
        raw = response.read(30_000_001)
    if len(raw) > 30_000_000:
        raise ValueError('Response exceeds size limit')
    return raw

class DownloadForm(HTMLParser):
    def __init__(self):
        super().__init__(); self.active = False; self.fields = {}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form': self.active = attrs.get('id') == 'file_down'
        if tag == 'input' and self.active and 'name' in attrs:
            self.fields[attrs['name']] = attrs.get('value', '')
    def handle_endtag(self, tag):
        if tag == 'form': self.active = False

def parse_bars(raw, period, asof, quarantine_conflicting_days=False):
    """Return validated UTC daily last closes and a gap/partial-day audit."""
    days = {}; previous = None; count = 0; gaps = []; first = None; last = None
    seen_day=None; seen={}; quarantined=set(); identical=0; conflicting=0
    for row in csv.reader(io.StringIO(raw.decode('utf-8-sig')), delimiter=';'):
        if len(row) != 6: raise ValueError('Expected six HistData M1 fields')
        s=row[0]
        if not MINUTE_STAMP.fullmatch(s): raise ValueError('Invalid minute timestamp format')
        local=dt.datetime.fromisoformat(s[:4]+'-'+s[4:6]+'-'+s[6:8]+'T'+s[9:11]+':'+s[11:13]+':'+s[13:15])
        if not row[0].startswith(period): raise ValueError('Bar outside requested local period')
        instant = local.replace(tzinfo=EST).astimezone(dt.timezone.utc)
        if instant.second != 0 or instant >= asof: raise ValueError('Future/non-minute bar')
        o,h,l,c = [float(x) for x in row[1:5]]
        if any(not math.isfinite(x) or x <= 0 for x in (o,h,l,c)) or l > min(o,c) or h < max(o,c) or l > h:
            raise ValueError('Invalid OHLC bar')
        if float(row[5]) != 0: raise ValueError('Unexpected nonzero volume: verify source contract')
        day = instant.date().isoformat()
        if seen_day is not None and day<seen_day: raise ValueError('Unordered UTC days')
        if day!=seen_day: seen={};seen_day=day
        key=instant.isoformat(); values=(o,h,l,c)
        if key in seen or previous is not None and instant<=previous:
            if not quarantine_conflicting_days: raise ValueError('Duplicate or unordered minute')
            if seen.get(key)==values:
                identical+=1;continue
            # A repeated clock hour with differing values is ambiguous. Reject
            # the whole UTC day rather than choosing a timestamp/price silently.
            quarantined.add(day);conflicting+=1
        seen[key]=values
        if previous is not None:
            minutes = (instant-previous).total_seconds()/60
            if minutes > 1: gaps.append(minutes)
        previous = instant; first = first or instant; last = instant; count += 1
        if day >= asof.date().isoformat(): continue
        entry = days.setdefault(day, {'date':day,'price':c,'firstMinuteAt':instant.isoformat(), 'lastMinuteAt':instant.isoformat(),'observedMinutes':0})
        entry.update(price=c, lastMinuteAt=instant.isoformat()); entry['observedMinutes'] += 1
    if not count: raise ValueError('Empty minute file')
    return [r for d,r in days.items() if d not in quarantined], {'minuteRows':count,'firstMinuteAt':first.isoformat(),'lastMinuteAt':last.isoformat(),
        'identicalDuplicateMinutesRemoved':identical,'ambiguousMinuteRows':conflicting,'quarantinedUtcDays':sorted(quarantined),
        'gapsOverOneMinute':len(gaps),'maxGapMinutes':max(gaps,default=0),
        'gapMeaning':'Includes normal market closures; no missing bar was filled'}

def histdata(period, asof):
    year = period[:4]; month = '/' + str(int(period[4:])) if len(period)==6 else ''
    url = f'https://www.histdata.com/download-free-forex-data/?/ascii/1-minute-bar-quotes/XAUUSD/{year}{month}'
    path = CACHE / f'histdata-{period}.zip'
    if path.exists(): raw = path.read_bytes()
    else:
        form = DownloadForm(); form.feed(download(url).decode())
        expected = {'date':year,'datemonth':period,'platform':'ASCII','timeframe':'M1','fxpair':'XAUUSD'}
        if any(form.fields.get(k)!=v for k,v in expected.items()) or not form.fields.get('tk'):
            raise ValueError('Requested download form missing or changed')
        raw = download('https://www.histdata.com/get.php', urllib.parse.urlencode(form.fields).encode(), {'Referer':url})
        if not zipfile.is_zipfile(io.BytesIO(raw)): raise ValueError('Response is not a ZIP archive')
        path.write_bytes(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = [x for x in archive.infolist() if x.filename.endswith('.csv')]
        expected_name = f'DAT_ASCII_XAUUSD_M1_{period}.csv'
        if len(names)!=1 or names[0].filename!=expected_name or names[0].file_size>50_000_000:
            raise ValueError('Unexpected archive contents')
        rows, audit = parse_bars(archive.read(names[0]), period, asof, quarantine_conflicting_days=True)
    return rows, {'period':period,'url':url,'rawSha256':hashlib.sha256(raw).hexdigest(),**audit,'status':'accepted_bid_research'}

def parse_vintages(raw, series, dates, start):
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    headers = ['observation_date'] + [series+'_'+d.replace('-','') for d in dates]
    if reader.fieldnames != headers: raise ValueError('Wrong ALFRED vintage columns')
    columns = {d:[] for d in dates}; seen = set()
    for row in reader:
        day = row['observation_date']; dt.date.fromisoformat(day)
        if day in seen: raise ValueError('Duplicate observation date')
        seen.add(day)
        for vintage in dates:
            value = row[series+'_'+vintage.replace('-','')]
            if value in ('','.'): continue
            value = float(value)
            if not math.isfinite(value) or day > vintage: raise ValueError('Future or nonfinite vintage observation')
            if day >= start: columns[vintage].append((day,value))
    records = []
    for vintage, observations in columns.items():
        if not observations: continue  # series may not yet exist in early years
        day, value = max(observations)
        record={'feature':SERIES[series],'value':value,'observedAt':day+'T00:00:00Z',
            'availableAt':vintage+'T23:59:59.999Z','source':'ALFRED:'+series,'vintage':vintage,
            'availabilityPrecision':'day','availabilityPolicy':'conservative_end_of_requested_vintage_day',
            'sampling':'monthly_as_of_snapshot; not every release', 'historicalSnapshot':True}
        records.append(record)
        if series=='CPIAUCSL':
            prior=dt.date.fromisoformat(day).replace(year=int(day[:4])-1).isoformat()
            previous=dict(observations).get(prior)
            if previous is not None and previous>0:
                records.append({**record,'feature':'us_cpi_yoy_pct','value':100*(value/previous-1),
                    'derivation':'12-month percent change using two observations from the same ALFRED vintage'})
    return records, {d:len(v) for d,v in columns.items()}

def alfred(series, year, end, start):
    dates = [f'{year}-{m:02}-01' for m in range(1,13) if f'{year}-{m:02}-01' <= end]
    query = urllib.parse.urlencode({'id':','.join([series]*len(dates)),'cosd':start,'vintage_date':','.join(dates)})
    url = 'https://alfred.stlouisfed.org/graph/alfredgraph.csv?'+query
    path = CACHE / f'alfred-{series}-{year}.csv'
    raw = path.read_bytes() if path.exists() else download(url)
    try:
        records, counts = parse_vintages(raw,series,dates,start)
    except ValueError:
        if OFFLINE or not path.exists(): raise
        # The current-year cache may have fewer requested months. Refresh the
        # official export rather than silently reuse mismatched vintage columns.
        raw=download(url);records,counts=parse_vintages(raw,series,dates,start)
    path.write_bytes(raw)
    return records, {'series':series,'year':year,'url':url,'rawSha256':hashlib.sha256(raw).hexdigest(),
        'vintageObservationCounts':counts,'featureRecords':len(records),'status':'accepted_monthly_vintage_snapshots'}

def collect(start_year=2016, end_year=2026):
    if not 1900<=start_year<=end_year<=dt.datetime.now(dt.timezone.utc).year:
        raise ValueError('Invalid research year range')
    CACHE.mkdir(parents=True,exist_ok=True); ROOT.joinpath('reports').mkdir(exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc); records=[]; daily={}; manifest=[]
    previous_path=ROOT/'reports/source-research-20261012.json'
    previous=json.loads(previous_path.read_text()) if OFFLINE and previous_path.exists() else {}
    tasks=[]
    for year in range(start_year,min(end_year,now.year)+1):
        periods = [str(year)] if year<now.year else [f'{year}{m:02}' for m in range(1,now.month)]
        tasks.extend(('gold',p) for p in periods)
        tasks.extend(('macro',(s,year)) for s in SERIES)
    def run(task):
        kind, item=task
        try:
            rows,meta = histdata(item,now) if kind=='gold' else alfred(item[0],item[1],now.date().isoformat(),f'{start_year}-01-01')
            return kind, rows, meta
        except Exception as error:
            request_key=item if isinstance(item,str) else list(item)
            old=next((r for r in previous.get('requests',[]) if r.get('request')==request_key),None)
            return kind, [], old or {'request':item,'status':'unavailable','error':str(error)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for kind, rows, meta in pool.map(run,tasks):
            manifest.append(meta)
            if kind=='macro': records.extend(rows)
            else:
                for row in rows:
                    # UTC boundary can span adjacent local-month archives.
                    old=daily.get(row['date'])
                    if old:
                        winner = row if row['lastMinuteAt']>old['lastMinuteAt'] else old
                        first=min(row['firstMinuteAt'],old['firstMinuteAt'])
                        daily[row['date']]={**winner,'firstMinuteAt':first,'observedMinutes':row['observedMinutes']+old['observedMinutes']}
                    else: daily[row['date']]=row
            print(json.dumps({'kind':kind,**{k:meta[k] for k in ('series','year','period','status','error') if k in meta}}),flush=True)
    gold=sorted(daily.values(),key=lambda r:r['date']); received=stamp()
    # The final local archive can end part-way through a UTC day. Omit the
    # terminal UTC day conservatively until the next local archive is present.
    boundary_day=gold[-1]['date'] if gold else None
    if gold: gold=gold[:-1]
    payload={'source':'HistData XAUUSD bid M1 aggregated UTC','attribution':'HistData.com https://www.histdata.com/f-a-q/',
        'metal':'XAU','unit':'USD per troy ounce','grain':'daily','priceKind':'last observed M1 bid close in completed UTC day',
        'receivedAt':received,'points':[{'date':r['date'],'price':r['price']} for r in gold]}
    ROOT.joinpath('data/histdata.json').write_text(json.dumps(payload))
    ROOT.joinpath('data/histdata-day-audit.json').write_text(json.dumps(gold))
    ROOT.joinpath('data/macro-vintages.json').write_text(json.dumps(records))
    report={'schemaVersion':1,'runAt':received,'requests':manifest,'gold':{'rows':len(gold),'from':gold[0]['date'] if gold else None,'to':gold[-1]['date'] if gold else None,
        'historySha256':hashlib.sha256(json.dumps(payload['points'],sort_keys=True).encode()).hexdigest(),
        'daysWithFewerThan60Minutes':sum(r['observedMinutes']<60 for r in gold),
        'terminalUtcDayExcluded':boundary_day,
        'measurement':'UTC daily last observed bid minute close; no gap filling; partial days explicitly retained'},
        'macro':{'records':len(records),'fromVintage':min((r['vintage'] for r in records),default=None),
        'toVintage':max((r['vintage'] for r in records),default=None),'series':SERIES,
        'use':'Historical point-in-time context at monthly snapshot resolution, conservative end-of-day availability. Not an exact release calendar.'},
        'limitations':['Raw archives are current downloaded price vintages, not immutable historical price snapshots',
        'HistData provides no reliability certification; vendor upstream independence unproven',
        'Volume field zero means unavailable; it is not measured traded volume',
        'Current incomplete local month is not downloaded; no claim of freshness',
        'Raw vendor files are not redistributed; public reports contain provenance and derived metrics']}
    ROOT.joinpath('reports/source-research-20261012.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'gold':report['gold'],'macro':report['macro'],'failures':[m for m in manifest if m['status']=='unavailable']},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--start-year',type=int,default=2016);parser.add_argument('--end-year',type=int,default=2026)
    parser.add_argument('--offline',action='store_true',help='Rebuild only cached files, without network retries')
    args=parser.parse_args(); OFFLINE=args.offline; collect(args.start_year,args.end_year)

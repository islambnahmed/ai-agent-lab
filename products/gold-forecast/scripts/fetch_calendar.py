"""BLS published calendar, available from fetch time, never backdated."""
import datetime as dt
import hashlib
import json
import re
from zoneinfo import ZoneInfo
from collect_research import ROOT, CACHE, download, stamp

def parse_ics(raw, known_at):
    text=re.sub(r'\r?\n[ \t]', '', raw.decode('utf-8-sig'))
    if 'BEGIN:VCALENDAR' not in text: raise ValueError('Not an iCalendar')
    events=[]
    for block in text.split('BEGIN:VEVENT')[1:]:
        block=block.split('END:VEVENT')[0]
        summary=re.search(r'^SUMMARY:(.+)$',block,re.M)
        start=re.search(r'^DTSTART;TZID=US-Eastern:(\d{8}T\d{6})\s*$',block,re.M)
        if not summary or not start: raise ValueError('Unsupported event fields/timezone')
        if not any(x in summary[1] for x in ('Consumer Price Index','Employment Situation','Producer Price Index')): continue
        instant=dt.datetime.strptime(start[1],'%Y%m%dT%H%M%S').replace(tzinfo=ZoneInfo('America/New_York')).astimezone(dt.timezone.utc)
        events.append({'event':summary[1],'scheduledAt':instant.isoformat().replace('+00:00','Z'),'knownAt':known_at,
            'source':'BLS','status':'scheduled; calendar is revisable, not proof of actual publication'})
    if not events: raise ValueError('No selected events found')
    return sorted(events,key=lambda r:r['scheduledAt'])

def main():
    url='https://www.bls.gov/schedule/news_release/bls.ics';raw=download(url);received=stamp()
    events=parse_ics(raw,received); CACHE.mkdir(parents=True,exist_ok=True);CACHE.joinpath('bls.ics').write_bytes(raw)
    ROOT.joinpath('data/calendar.json').write_text(json.dumps(events,indent=2)+'\n')
    report={'url':url,'receivedAt':received,'rawSha256':hashlib.sha256(raw).hexdigest(),'events':len(events),
        'from':events[0]['scheduledAt'],'to':events[-1]['scheduledAt'],'upcoming':[r for r in events if r['scheduledAt']>received],
        'use':'Current/future context only. Historical event-calendar vintages were not retrieved.'}
    ROOT.joinpath('reports').mkdir(exist_ok=True);ROOT.joinpath('reports/calendar-sources-20261012.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'events':len(events),'upcoming':len(report['upcoming'])}))

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Offline single-snapshot SEO heuristics; not a ranking/indexing guarantee."""
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin
from pathlib import Path
import argparse, json, re, sys

def weburl(url):
    """Conservative syntactic HTTP(S) URL validation, not DNS verification."""
    try:
        if not isinstance(url, str) or not url or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in url):
            return False
        p = urlsplit(url)
        if p.scheme.lower() not in ('http', 'https') or not p.netloc or '@' in p.netloc or '\\' in p.netloc:
            return False
        if not p.hostname or '%' in p.hostname:
            return False
        port = p.port  # Access validates numeric port and its allowed range.
        return port is None or port > 0
    except (ValueError, TypeError, AttributeError):
        return False

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.head=False; self.title=None; self.h=None; self.anchor=None; self.script=None; self.suppressed=0
        self.lang=[]; self.titles=[]; self.meta=[]; self.canonicals=[]; self.alternates=[]
        self.headings=[]; self.images=[]; self.anchors=[]; self.jsonld=[]
    def close(self):
        super().close()
        # A heading can remain open at EOF in malformed but common HTML.
        if self.h is not None:
            self.h['text'] = ' '.join(self.h['text'].split())
            self.headings.append(self.h)
            self.h = None

    def handle_starttag(self,tag,attrs):
        a={k.lower():v or '' for k,v in attrs if k}
        if tag=='html': self.lang.append(a.get('lang',''))
        if tag=='head': self.head=True
        if tag=='title' and self.head: self.title=''
        if tag=='meta' and self.head: self.meta.append(a)
        if tag=='link' and self.head:
            rel=a.get('rel','').lower().split()
            if 'canonical' in rel: self.canonicals.append(a.get('href',''))
            if 'alternate' in rel and 'hreflang' in a: self.alternates.append((a['hreflang'],a.get('href','')))
        if tag in ('h1','h2','h3','h4','h5','h6'): self.h={'level':int(tag[1]),'text':''}
        if tag=='img':
            self.images.append(a)
            if self.anchor is not None: self.anchors[self.anchor]['text']+=' '+a.get('alt','')
        if tag=='a':
            self.anchors.append({'href':a.get('href',''),'text':'','label':a.get('aria-label','')})
            self.anchor=len(self.anchors)-1
        if tag=='script' and a.get('type','').lower()=='application/ld+json': self.script=''
        if tag in ('script','style'): self.suppressed+=1
    def handle_data(self,data):
        if self.title is not None: self.title+=data[:200000]
        if self.h is not None and not self.suppressed: self.h['text']+=data[:200000]
        if self.anchor is not None and not self.suppressed: self.anchors[self.anchor]['text']+=data[:200000]
        if self.script is not None: self.script+=data[:200000]
    def handle_endtag(self,tag):
        if tag=='title' and self.title is not None:
            self.titles.append(' '.join(self.title.split())); self.title=None
        if tag in ('h1','h2','h3','h4','h5','h6') and self.h and self.h['level']==int(tag[1]):
            self.h['text']=' '.join(self.h['text'].split()); self.headings.append(self.h); self.h=None
        if tag=='a': self.anchor=None
        if tag=='script' and self.script is not None: self.jsonld.append(self.script); self.script=None
        if tag in ('script','style') and self.suppressed: self.suppressed-=1
        if tag=='head': self.head=False

def audit(html,page_url):
    if not weburl(page_url): raise ValueError('Absolute HTTP(S) page URL required')
    p=Parser(); p.feed(html); p.close()
    f=[]
    def add(code,severity,detail): f.append({'code':code,'severity':severity,'detail':detail})
    if len(p.titles)>1: add('title_duplicate','error','Multiple titles')
    elif not p.titles or not p.titles[0]: add('title_missing','error','Missing nonempty title')
    elif not 25<=len(p.titles[0])<=65: add('title_length','warning','Title length outside 25–65 heuristic')
    ds=[m.get('content','') for m in p.meta if m.get('name','').lower()=='description']
    if len(ds)>1: add('description_duplicate','warning','Multiple descriptions')
    elif not ds or not ds[0].strip(): add('description_missing','warning','Missing description')
    elif not 70<=len(ds[0])<=170: add('description_length','info','Description length outside 70–170 heuristic')
    if not p.lang or not p.lang[0].strip(): add('lang_missing','warning','Missing html lang')
    if not any(m.get('name','').lower()=='viewport' for m in p.meta): add('viewport_missing','info','No viewport meta')
    robots=[m.get('content','').lower() for m in p.meta if m.get('name','').lower() in ('robots','googlebot')]
    for directive in ('noindex','nofollow'):
        if any(re.search(r'(?<![a-z])'+directive+r'(?![a-z])',s) for s in robots):
            add(directive,'info','Explicit '+directive+' directive; may be intentional')
    if not p.canonicals: add('canonical_missing','warning','Missing canonical')
    elif len(p.canonicals)>1: add('canonical_multiple','error','Multiple canonicals')
    else:
        c=p.canonicals[0]
        if not weburl(c): add('canonical_invalid','error','Canonical must be absolute HTTP(S)')
        elif urlsplit(c).scheme.lower()=='http': add('canonical_http','warning','HTTP canonical')
        if weburl(c) and urlsplit(c).netloc.lower()!=urlsplit(page_url).netloc.lower():
            add('canonical_external','info','Canonical points to another host; verify intent')
    h1=[h for h in p.headings if h['level']==1]
    if not h1: add('h1_missing','warning','No H1')
    elif len(h1)>1: add('h1_multiple','info','Multiple H1; may be intentional')
    if any(not h['text'] for h in h1): add('h1_empty','warning','Empty H1')
    n=sum('alt' not in im for im in p.images)
    if n: add('image_alt_missing','warning',str(n)+' images lack alt')
    n=sum('alt' in im and not im['alt'] for im in p.images)
    if n: add('image_alt_empty','info',str(n)+' images have empty alt; possibly decorative')
    n=sum(not (a['text']+a['label']).strip() for a in p.anchors)
    if n: add('link_name_missing','warning',str(n)+' links lack text or aria-label')
    seen=set()
    for lang,href in p.alternates:
        if lang.lower() in seen: add('hreflang_duplicate','warning','Duplicate '+lang)
        seen.add(lang.lower())
        if not weburl(href): add('hreflang_invalid','warning','Nonabsolute hreflang '+lang)
    for i,block in enumerate(p.jsonld):
        try: json.loads(block)
        except json.JSONDecodeError: add('jsonld_invalid','error','Invalid JSON-LD block '+str(i+1))
    f.sort(key=lambda x:(('error','warning','info').index(x['severity']),x['code'],x['detail']))
    internal=set()
    for anchor in p.anchors:
        href=anchor['href'].strip()
        if not href or href.startswith('#'):
            continue  # Empty/fragment-only targets are not links to other pages.
        target=urljoin(page_url,href)
        if weburl(target) and urlsplit(target).netloc.lower()==urlsplit(page_url).netloc.lower():
            internal.add(target.split('#',1)[0])
    return {'schema_version':1,'page_url':page_url,
            'summary':{'errors':sum(x['severity']=='error' for x in f),
                       'warnings':sum(x['severity']=='warning' for x in f),
                       'infos':sum(x['severity']=='info' for x in f),
                       'images':len(p.images),'internal_links_unique':len(internal)},
            'findings':f,
            'scope':'Offline single-HTML heuristics; cannot verify HTTP headers, robots.txt, JS DOM, Google indexation, backlinks, hreflang reciprocity or rankings.'}

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('file',type=Path); a.add_argument('--url',required=True)
    a.add_argument('--fail-on',choices=('error','warning','never'),default='error')
    args=a.parse_args()
    if args.file.stat().st_size>2_000_000: a.error('HTML file exceeds 2 MB')
    try: result=audit(args.file.read_text(encoding='utf-8'),args.url)
    except (OSError,UnicodeError,ValueError) as e: a.error(str(e))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    s=result['summary']
    return int((args.fail_on=='error' and s['errors']>0) or
               (args.fail_on=='warning' and (s['errors']>0 or s['warnings']>0)))
if __name__=='__main__': sys.exit(main())

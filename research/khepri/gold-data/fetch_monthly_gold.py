#!/usr/bin/env python3
"""Fetch independently licensed monthly gold prices; no credentials or third-party packages."""
import csv, hashlib, io, json, pathlib, urllib.request, datetime as dt
URL="https://raw.githubusercontent.com/datasets/gold-prices/main/data/monthly-processed.csv"
BASE=pathlib.Path(__file__).resolve().parent
def main():
    req=urllib.request.Request(URL,headers={"User-Agent":"AI-Agent-Lab-gold-research/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        payload=r.read(2_000_000)
    raw=list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))
    if not raw or set(raw[0])!={"Date","Price"}: raise ValueError("Unexpected source schema")
    clean=[]; prev=None
    for row in raw:
        d=dt.date.fromisoformat(row["Date"]);p=float(row["Price"])
        if d.year<1960: continue  # Before 1960 source repeats annual values monthly
        if d.day!=1 or (prev and d<=prev) or not 0<p<100000: raise ValueError("Invalid monthly record")
        clean.append((d.isoformat(),p));prev=d
    if len(clean)<500: raise ValueError("Insufficient history")
    dest=BASE/"gold_monthly_1960plus.csv"
    with dest.open("w",newline="") as f:
        w=csv.writer(f);w.writerow(["date","usd_per_troy_ounce"]);w.writerows(clean)
    manifest={"source":URL,"upstream":"World Bank Commodity Markets Pink Sheet via datasets/gold-prices","license":"ODC-PDDL-1.0 per dataset package","frequency":"monthly average; not daily spot","retrieved_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"source_sha256":hashlib.sha256(payload).hexdigest(),"rows":len(clean),"first":clean[0][0],"last":clean[-1][0],"caveat":"Monthly period averages cannot be used as if known at the start of the month. For backtests, make available only after period end and verified publication lag."}
    (BASE/"gold_monthly_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))
if __name__=="__main__":main()

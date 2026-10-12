#!/usr/bin/env python3
"""Strict historical gold CSV validation. Python stdlib only."""
import csv, datetime as dt, math, sys
REQUIRED = ("date","close","source","asset","currency","unit","observed_at_utc")
def validate(path):
    rows=[]
    with open(path,newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        if tuple(reader.fieldnames or ()) != REQUIRED:
            raise ValueError("columns must be: "+",".join(REQUIRED))
        last=None; identity=None
        for line,r in enumerate(reader,2):
            if not all(r.get(k,"").strip() for k in REQUIRED):
                raise ValueError(f"line {line}: missing field")
            date=dt.date.fromisoformat(r["date"])
            price=float(r["close"])
            if not math.isfinite(price) or price<=0: raise ValueError(f"line {line}: invalid price")
            stamp=dt.datetime.fromisoformat(r["observed_at_utc"].replace("Z","+00:00"))
            if stamp.tzinfo is None or stamp.utcoffset()!=dt.timedelta(0):
                raise ValueError(f"line {line}: observed_at_utc must be UTC")
            if stamp.date()<date: raise ValueError(f"line {line}: observation precedes session date")
            if last is not None and date<=last: raise ValueError(f"line {line}: dates not strictly increasing")
            ident=(r["source"],r["asset"],r["currency"],r["unit"])
            if identity is not None and ident!=identity: raise ValueError(f"line {line}: mixed instruments/providers")
            identity=ident;last=date;rows.append((date,price,stamp))
    if not rows: raise ValueError("empty dataset")
    return rows
if __name__=="__main__":
    try:
        rows=validate(sys.argv[1])
        print(f"PASS: {len(rows)} rows, {rows[0][0]} through {rows[-1][0]}")
    except (ValueError,IndexError,OSError) as exc:
        print(f"FAIL: {exc}",file=sys.stderr);sys.exit(1)

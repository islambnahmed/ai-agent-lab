#!/usr/bin/env python3
"""Reproducible monthly gold walk-forward baseline benchmark. Standard library only.
Dataset: gold_monthly_1960plus.csv. Assumes each prior month's average is available
by next forecast origin; actual publication delays are not verified. This is an
illustrative monthly backtest, NOT a point-in-time trading evaluation.
"""
import csv, math, pathlib
rows=list(csv.DictReader((pathlib.Path(__file__).parent/"gold_monthly_1960plus.csv").open()))
dates=[r["date"] for r in rows]
prices=[float(r["usd_per_troy_ounce"]) for r in rows]
assert len(prices)==801 and all(dates[i]>dates[i-1] and prices[i]>0 for i in range(1,len(prices)))
origins=[i for i,d in enumerate(dates) if d>="2016-01-01"]
models={
 "last_price":lambda i:prices[i-1],
 "mean_3m":lambda i:sum(prices[i-3:i])/3,
 "mean_12m":lambda i:sum(prices[i-12:i])/12,
 "drift_3m":lambda i:prices[i-1]+(prices[i-1]-prices[i-4])/3,
 "drift_12m":lambda i:prices[i-1]+(prices[i-1]-prices[i-13])/12,
}
for name,predict in models.items():
 errors=[prices[i]-predict(i) for i in origins]
 mae=sum(map(abs,errors))/len(errors)
 rmse=math.sqrt(sum(e*e for e in errors)/len(errors))
 mape=sum(abs(e)/prices[i] for e,i in zip(errors,origins))/len(errors)*100
 direction=sum((prices[i]-prices[i-1])*(predict(i)-prices[i-1])>0 for i in origins)/len(origins)*100
 print(f"{name:14s} N={len(origins)} MAE={mae:.3f} RMSE={rmse:.3f} MAPE={mape:.3f}% direction={direction:.2f}%")

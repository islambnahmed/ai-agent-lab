"""Cycle 170: compact reproduction. Rounded World Bank Pink Sheet gold USD/toz.
Snapshot PDF dates are not certified first-publication vintages.
"""
from datetime import date
from statistics import mean
BATCHES = [
 ('2025-02-03','2024-10',[2690,2651,2648]),
 ('2025-04-02','2025-01',[2710,2895,2983]),
 ('2025-07-02','2025-04',[3218,3309,3353]),
 ('2025-10-02','2025-07',[3340,3368,3668]),
 ('2026-01-06','2025-10',[4058,4087,4309]),
 ('2026-04-02','2026-01',[4753,5020,4856]),
 ('2026-07-02','2026-04',[4721,4587,4228]),
 ('2026-10-02','2026-07',[4073,4411,4319]),
]
def add_month(s,n):
 y,m=map(int,s.split('-'));z=y*12+m-1+n
 return f'{z//12:04d}-{z%12+1:02d}'
def evaluate(prequarter):
 out=[]
 for i in range(2,len(BATCHES)):
  issue,first,actual=BATCHES[i]
  cutoff,known_start,known=BATCHES[i-(2 if prequarter else 1)]
  assert date.fromisoformat(cutoff)<date.fromisoformat(issue)
  for j,truth in enumerate(actual):
   target=add_month(first,j);h=j+(4 if prequarter else 1)
   if prequarter: assert cutoff<target+'-01'
   persistence=known[-1]
   linear3=known[-1]+h*(known[-1]-known[-3])/2
   out.append((target,truth,persistence,linear3))
 return out
def mae(rows,idx):
 return round(mean(abs(r[idx]-r[1]) for r in rows),2)
if __name__=='__main__':
 late=evaluate(False);pre=evaluate(True)
 assert len(late)==len(pre)==18
 assert [r[0] for r in late]==[r[0] for r in pre]
 for name,rows in [('late',late),('prequarter',pre),
                   ('late_2025',[r for r in late if r[0].startswith('2025')]),
                   ('late_2026',[r for r in late if r[0].startswith('2026')])]:
  print(name,len(rows),'persistence',mae(rows,2),'linear3',mae(rows,3))
 assert (mae(late,2),mae(late,3))==(327.06,269.89)
 assert (mae(pre,2),mae(pre,3))==(662.17,512.78)

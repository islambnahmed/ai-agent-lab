/**
 * Worker A: scalable, as-of-capture walk-forward baseline benchmark.
 * A drop-in research alternative to walkForwardBenchmark, not a live forecaster.
 * Runtime O(n log n + n * trendLookback * log n), rather than O(n^2).
 * Captures arriving out of provider order and simultaneous batches are supported.
 * This does NOT authenticate historical capture timestamps or data vendors.
 */
import {validateObservations, fixedBaselines} from './walkforward-benchmark.mjs';

const HOUR = 3_600_000;
const DAY = 24 * HOUR;
const ensure = (v, m) => { if (!v) throw new Error(m); };
const avg = xs => xs.reduce((a,b)=>a+b,0)/xs.length;

class Fenwick {
  constructor(n) { this.n=n; this.tree=new Int32Array(n+1); this.count=0; }
  add(index) { for(let i=index+1;i<=this.n;i+=i&-i)this.tree[i]++; this.count++; }
  /** 0-based index of the k-th present item, with k 1-based. */
  kth(k) {
    ensure(Number.isSafeInteger(k) && k>=1 && k<=this.count, 'Invalid order statistic');
    let pos=0, bit=1;
    while(bit*2<=this.n)bit*=2;
    for(;bit;bit>>=1){const next=pos+bit;if(next<=this.n && this.tree[next]<k){k-=this.tree[next];pos=next;}}
    return pos;
  }
}
function firstAtOrAfter(data, time) {
  let lo=0,hi=data.length;
  while(lo<hi){const mid=(lo+hi)>>>1;if(data[mid].updatedMs<time)lo=mid+1;else hi=mid;}
  return lo;
}
export function walkForwardScalable(rows, {
  horizonMs=HOUR,minHistory=3,trendLookback=3,maxQuoteAgeMs=HOUR,
  targetToleranceMs=0,maxTargetCaptureDelayMs=5*60_000,
  requireProvenance=false,horizonAnchor='observation',
}={}) {
  ensure(Number.isSafeInteger(horizonMs)&&horizonMs>0&&horizonMs<=30*DAY,'Invalid horizon');
  ensure(Number.isSafeInteger(minHistory)&&minHistory>=2&&minHistory<=1000,'Invalid minimum history');
  ensure(Number.isSafeInteger(trendLookback)&&trendLookback>=2&&trendLookback<=minHistory,'Invalid trend lookback');
  ensure(Number.isSafeInteger(maxQuoteAgeMs)&&maxQuoteAgeMs>=0&&maxQuoteAgeMs<=30*DAY,'Invalid quote age');
  ensure(Number.isSafeInteger(targetToleranceMs)&&targetToleranceMs>=0&&targetToleranceMs<=HOUR,'Invalid target tolerance');
  ensure(Number.isSafeInteger(maxTargetCaptureDelayMs)&&maxTargetCaptureDelayMs>=0&&maxTargetCaptureDelayMs<=HOUR,'Invalid target capture delay');
  ensure(['observation','issuance'].includes(horizonAnchor),'Invalid horizon anchor');
  const data=validateObservations(rows,{requireProvenance});
  const events=data.map((row,index)=>({index,capturedMs:row.capturedMs}));
  events.sort((a,b)=>a.capturedMs-b.capturedMs||a.index-b.index);
  const seen=new Fenwick(data.length);
  const byAnchor=[];
  const skipped={warmup:0,stale:0,targetMissing:0,targetNotFuture:0,targetCaptureLate:0,duplicateAnchor:0};
  for(let start=0;start<events.length;){
    let end=start+1;
    while(end<events.length&&events[end].capturedMs===events[start].capturedMs)end++;
    // A batch is visible atomically: do not use an earlier row from the batch
    // while pretending later rows captured at the same instant were unknown.
    for(let j=start;j<end;j++)seen.add(events[j].index);
    const lastIndex=seen.kth(seen.count);
    const last=data[lastIndex];
    for(let j=start;j<end;j++){
      const index=events[j].index;
      const anchor=data[index];
      if(seen.count<minHistory){skipped.warmup++;continue;}
      if(lastIndex!==index){skipped.duplicateAnchor++;continue;}
      if(anchor.capturedMs-last.updatedMs>maxQuoteAgeMs){skipped.stale++;continue;}
      const targetMs=(horizonAnchor==='issuance'?anchor.capturedMs:last.updatedMs)+horizonMs;
      const t=firstAtOrAfter(data,targetMs);
      const target=t<data.length&&data[t].updatedMs<=targetMs+targetToleranceMs?data[t]:null;
      if(!target){skipped.targetMissing++;continue;}
      if(target.updatedMs<=anchor.capturedMs||target.capturedMs<=anchor.capturedMs){skipped.targetNotFuture++;continue;}
      if(target.capturedMs-target.updatedMs>maxTargetCaptureDelayMs){skipped.targetCaptureLate++;continue;}
      const prior=[];
      for(let k=Math.min(trendLookback,seen.count)-1;k>=0;k--){
        prior.push(data[seen.kth(seen.count-k)]);
      }
      const prediction=fixedBaselines(prior,targetMs-last.updatedMs,trendLookback);
      byAnchor.push({index,forecast:Object.freeze({
        issuedAt:anchor.capturedAt,targetAt:target.updatedAt,
        effectiveLeadMs:target.updatedMs-anchor.capturedMs,
        nominalTargetAt:new Date(targetMs).toISOString(),targetLagMs:target.updatedMs-targetMs,
        targetCaptureDelayMs:target.capturedMs-target.updatedMs,
        trainingThrough:last.updatedAt,trainingCount:seen.count,
        targetCapturedAt:target.capturedAt,actual:target.price,
        ...prediction,
        persistenceAbsoluteError:Math.abs(prediction.persistence-target.price),
        driftAbsoluteError:Math.abs(prediction.drift-target.price),
      })});
    }
    start=end;
  }
  byAnchor.sort((a,b)=>a.index-b.index);
  const forecasts=byAnchor.map(x=>x.forecast);
  const summary=forecasts.length?Object.freeze({
    count:forecasts.length,
    persistenceMAE:avg(forecasts.map(x=>x.persistenceAbsoluteError)),
    driftMAE:avg(forecasts.map(x=>x.driftAbsoluteError)),
    persistenceRMSE:Math.sqrt(avg(forecasts.map(x=>x.persistenceAbsoluteError**2))),
    driftRMSE:Math.sqrt(avg(forecasts.map(x=>x.driftAbsoluteError**2))),
    driftStrictWinRate:forecasts.filter(x=>x.driftAbsoluteError<x.persistenceAbsoluteError).length/forecasts.length,
  }):Object.freeze({count:0,persistenceMAE:null,driftMAE:null,persistenceRMSE:null,driftRMSE:null,driftStrictWinRate:null});
  return Object.freeze({
    instrument:'Supplied XAU/USD price series (USD per troy ounce; basis explicitly labeled when known)',
    source:data[0].source,priceBasis:data[0].priceBasis,requireProvenance,
    horizonMs,horizonAnchor,minHistory,trendLookback,maxQuoteAgeMs,targetToleranceMs,maxTargetCaptureDelayMs,
    summary,skipped:Object.freeze(skipped),forecasts:Object.freeze(forecasts),
    caveat:'Fast as-of-capture research benchmark only; capture claims and provenance not independently authenticated. No proof of prospective registration, provider truth, or market skill.',
  });
}

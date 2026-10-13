/** Khepri experiment 154: causal, horizon-aware prequential interval audit.
 * Prices are synthetic. This is a research comparator, not a deployment policy.
 * At origin t, error for origin j is eligible only if j+h <= t.
 */
export function finiteQuantile(values, level=0.8) {
  if (!Array.isArray(values) || !values.length || !(level>0 && level<1) || values.some(x=>!Number.isFinite(x)||x<0))
    throw Error('invalid quantile inputs');
  const sorted=[...values].sort((a,b)=>a-b);
  return sorted[Math.min(sorted.length-1,Math.ceil((sorted.length+1)*level)-1)];
}
export function bandAt(prices,t,h,{method='rolling',window=250,staticEnd=550,level=0.8}={}) {
  if (!Array.isArray(prices)||!Number.isInteger(t)||!Number.isInteger(h)||h<1||t<1||t>=prices.length||!Number.isInteger(window)||window<20||!Number.isInteger(staticEnd)||staticEnd<20)
    throw Error('invalid index or settings');
  if(!['rolling','static'].includes(method))throw Error('unknown method');
  const lastEligible=t-h;
  const end=method==='static'?Math.min(lastEligible,staticEnd-1):lastEligible;
  const start=method==='static'?0:Math.max(0,end-window+1);
  if(end<start || end-start+1<20) return null;
  const errors=[];
  for(let j=start;j<=end;j++){
    const origin=prices[j],target=prices[j+h];
    if(!Number.isFinite(origin)||origin<=0||!Number.isFinite(target)||target<=0)throw Error('invalid prices');
    errors.push(Math.abs(target/origin-1));
  }
  return {band:finiteQuantile(errors,level),trainN:errors.length,firstOrigin:start,lastOrigin:end,lastMaturedAt:end+h};
}
export function evaluate(prices,h,{evalStart=850,evalEnd=prices.length-h-1,window=250,staticEnd=550,stride=1}={}) {
  if(!Number.isInteger(stride)||stride<1)throw Error('invalid stride');
  const result={};
  for(const method of ['static','rolling']){
    let n=0,hit=0,sumBand=0;const observations=[];
    for(let t=evalStart;t<=evalEnd;t+=stride){
      if(t+h>=prices.length)break;
      const x=bandAt(prices,t,h,{method,window,staticEnd});
      if(!x)continue;
      const actualError=Math.abs(prices[t+h]/prices[t]-1),covered=actualError<=x.band;
      n++;hit+=covered;sumBand+=x.band;
      observations.push({t,covered,band:x.band,lastMaturedAt:x.lastMaturedAt});
    }
    result[method]={n,coverage:hit/n,meanHalfWidthPct:100*sumBand/n,observations};
  }
  return result;
}
export function syntheticPrices(seed=1,{n=2600,shiftAt=1300,preVol=0.007,postVol=0.007,shockRate=0,shockScale=4}={}){
  let state=seed>>>0;const rand=()=>{state=(1664525*state+1013904223)>>>0;return (state+0.5)/4294967296};
  const normal=()=>Math.sqrt(-2*Math.log(rand()))*Math.cos(2*Math.PI*rand());
  const prices=[2000];
  for(let i=1;i<n;i++){
    let r=normal()*(i>=shiftAt?postVol:preVol);
    if(rand()<shockRate)r*=shockScale;
    prices.push(prices.at(-1)*Math.exp(r));
  }
  return prices;
}
export function summarizeSegment(obs,from,to){
  const selected=obs.filter(x=>x.t>=from&&x.t<to);
  return {n:selected.length,coverage:selected.reduce((s,x)=>s+Number(x.covered),0)/selected.length,
    meanHalfWidthPct:100*selected.reduce((s,x)=>s+x.band,0)/selected.length};
}

/** Forecast elapsed calendar days until h future observed closes, NOT a guaranteed date.
 * Strictly uses matured historical h-step lags as of the current last observation.
 * Distribution-free guarantees do not apply under regime shifts or serial dependence.
 */
const DAY = /^\d{4}-\d{2}-\d{2}$/;
const MS = 86400000;
export function dayNumber(s) {
  if(typeof s !== 'string' || !DAY.test(s)) throw Error('Expected YYYY-MM-DD');
  const t=Date.parse(s+'T00:00:00Z');
  if(!Number.isFinite(t)||new Date(t).toISOString().slice(0,10)!==s) throw Error('Invalid date');
  return Math.round(t/MS);
}
export function isoDay(n){return new Date(n*MS).toISOString().slice(0,10)}
export function datesOf(series) {
  if(!Array.isArray(series)) throw Error('Expected series array');
  const days=series.map(x=>dayNumber(typeof x==='string'?x:x?.date));
  for(let i=1;i<days.length;i++) if(days[i]<=days[i-1])throw Error('Observations must have unique, increasing dates');
  return days;
}
function quantileSorted(sorted,p){
  const index=Math.min(sorted.length-1,Math.max(0,Math.ceil(p*sorted.length)-1));
  return sorted[index];
}
export function targetWindow(series,h,{minSamples=30,maxSamples=365,lowerTail=0.1,upperTail=0.9,driftGuard=true}={}) {
  if(!Number.isInteger(h)||h<1||h>365) throw Error('Invalid horizon');
  if(!Number.isInteger(minSamples)||minSamples<1||!Number.isInteger(maxSamples)||maxSamples<minSamples)throw Error('Invalid sample bounds');
  if(!(lowerTail>=0&&upperTail<=1&&lowerTail<upperTail))throw Error('Invalid quantiles');
  const days=datesOf(series), n=days.length;
  // Only origin j for which target j+h has already been observed is eligible.
  const available=n-h;
  if(available<minSamples) return {status:'insufficient',horizon:h,available,required:minSamples,targetDate:null};
  // Abstain when median of the last five inter-observation gaps differs by
  // more than 2x from the preceding up-to-90-gap median.
  // It cannot anticipate an abrupt change before enough new observations arrive.
  if(driftGuard && n>=45){
    const gaps=days.slice(1).map((d,i)=>d-days[i]);
    const recent=gaps.slice(-5),older=gaps.slice(-95,-5).sort((a,b)=>a-b);
    const floor=quantileSorted(older,0.05),ceiling=quantileSorted(older,0.95);
    const outside=recent.filter(v=>v<floor||v>ceiling).length;
    const medRecent=quantileSorted([...recent].sort((a,b)=>a-b),0.5);
    const medOlder=quantileSorted(older,0.5);
    const driftRatio=medRecent/medOlder;
    if(driftRatio>2||driftRatio<0.5)return {status:'cadence_shift',horizon:h,observedThrough:isoDay(days.at(-1)),
      targetDate:null,recentOutside:outside,baselineGapEnvelope:[floor,ceiling],driftRatio,
      caveat:'Recent observation cadence differs from historical calibration; suppress date window'};
  }
  const start=Math.max(0,available-maxSamples), lags=[];
  for(let j=start;j<available;j++)lags.push(days[j+h]-days[j]);
  lags.sort((a,b)=>a-b);
  const origin=days.at(-1);
  const low=quantileSorted(lags,lowerTail),median=quantileSorted(lags,0.5),high=quantileSorted(lags,upperTail);
  return {status:'estimated',horizon:h,horizonUnit:'future observed closes',n:lags.length,
    observedThrough:isoDay(origin),lowLagDays:low,medianLagDays:median,highLagDays:high,
    earliest:isoDay(origin+low),median:isoDay(origin+median),latest:isoDay(origin+high),
    targetDate:null,nominalHistoricalCentralPct:100*(upperTail-lowerTail),
    caveat:'Empirical historical lag window only; not an exact date or a guaranteed future coverage interval'};
}
export function walkForward(series,h,{start=120,...opts}={}){
  const days=datesOf(series),results=[];let suppressed=0;
  for(let i=Math.max(start,h+1);i+h<days.length;i++){
    const estimate=targetWindow(days.slice(0,i+1).map(isoDay),h,opts);
    if(estimate.status!=='estimated'){if(estimate.status==='cadence_shift')suppressed++;continue;}
    const lag=days[i+h]-days[i];
    results.push({origin:isoDay(days[i]),actual:isoDay(days[i+h]),actualLagDays:lag,
      low:estimate.lowLagDays,high:estimate.highLagDays,covered:lag>=estimate.lowLagDays&&lag<=estimate.highLagDays,
      naiveExact:lag===h,widthDays:estimate.highLagDays-estimate.lowLagDays});
  }
  const avg=f=>results.reduce((s,r)=>s+f(r),0)/results.length;
  return {horizon:h,n:results.length,suppressed,coveragePct:results.length?100*avg(r=>+r.covered):null,
    naiveExactPct:results.length?100*avg(r=>+r.naiveExact):null,
    meanWidthDays:results.length?avg(r=>r.widthDays):null,
    rows:results};
}

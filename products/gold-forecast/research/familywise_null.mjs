/** Seshat C94: simultaneous-horizon null calibration, NOT a market skill test. */
import {forecast} from '../forecast.mjs';
export const HORIZONS = Object.freeze([1,7,30]);
export function rng(seed) {
  let x=seed>>>0;
  return ()=>((x=(Math.imul(1664525,x)+1013904223)>>>0)+0.5)/4294967296;
}
export function syntheticRandomWalk(seed,n=500) {
  const u=rng(seed); let p=2500;
  const series=[];let date=new Date('2022-01-03T12:00:00Z');
  for(let i=0;i<n;i++) {
    const z=Math.sqrt(-2*Math.log(Math.max(1e-12,u())))*Math.cos(2*Math.PI*u());
    p*=Math.exp(0.01*z);
    series.push({date:date.toISOString().slice(0,10),price:p});
    do {date.setUTCDate(date.getUTCDate()+1)} while ([0,6].includes(date.getUTCDay()));
  }
  return series;
}
export function quantile(values,p) {
  if(!values.length||!Number.isFinite(p)||p<0||p>1)throw Error('invalid quantile');
  const sorted=[...values].sort((a,b)=>a-b);
  return sorted[Math.min(sorted.length-1,Math.max(0,Math.ceil(sorted.length*p)-1))];
}
export function analyze(series) {
  const perHorizon=HORIZONS.map(h=>{
    const result=forecast(series,h);
    const gain=(result.baseline.mae-result.audit.mae)/result.baseline.mae;
    // Consecutive h-session targets overlap. These are descriptive counts only.
    const holdout=series.length-Math.floor(series.length*0.8);
    return {h,model:result.model,gain,beat:result.beat,
      overlappingAudit:result.audit.n,disjointMax:Math.floor(holdout/h)};
  });
  return {perHorizon,anyBeat:perHorizon.some(x=>x.beat),
    anyGain5:perHorizon.some(x=>x.gain>0.05),
    maxGain:Math.max(...perHorizon.map(x=>x.gain))};
}
export function summarize(rows) {
  if(!rows.length)throw Error('empty results');
  const n=rows.length, gains=rows.map(x=>x.maxGain);
  const perHorizon=HORIZONS.map(h=>({h,beatCount:rows.filter(r=>r.perHorizon.find(x=>x.h===h).beat).length,
    gainOver5Count:rows.filter(r=>r.perHorizon.find(x=>x.h===h).gain>0.05).length,
    overlappingAudit:rows[0].perHorizon.find(x=>x.h===h).overlappingAudit,
    disjointMax:rows[0].perHorizon.find(x=>x.h===h).disjointMax}));
  return {n,anyBeatCount:rows.filter(x=>x.anyBeat).length,
    anyGain5Count:rows.filter(x=>x.anyGain5).length,
    maxGainQ90:quantile(gains,0.90),maxGainQ95:quantile(gains,0.95),
    maxGainQ99:quantile(gains,0.99),perHorizon,
    caveat:'Calibration applies only to this iid log-return synthetic null, model code, horizon menu, and sample length; no live-market inference.'};
}
export function simulate(firstSeed=1,count=1000) {
  if(!Number.isInteger(firstSeed)||firstSeed<1||!Number.isInteger(count)||count<1)throw Error('invalid simulation parameters');
  return summarize(Array.from({length:count},(_,i)=>analyze(syntheticRandomWalk(firstSeed+i))));
}

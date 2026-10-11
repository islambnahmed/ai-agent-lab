/** Khepri exp165: delayed-feedback adaptive conformal bands, monthly experimental data.
 * Maturity gate: only forecasts whose targetIndex < current origin may update alpha.
 * No guaranteed coverage under regime drift or correlated outcomes.
 */
import {buildForecasts,quantile} from './walkforward.mjs';
const clip=(x,a,b)=>Math.max(a,Math.min(b,x));
export function runAdaptive(rows,h,{gamma=0.05,targetMiss=0.2,minAlpha=0.01,maxAlpha=0.5,lookback=48,minCalibration=24,minHistory=60}={}){
 if(!(gamma>=0&&gamma<=1)||!(targetMiss>0&&targetMiss<1)||!(minAlpha>0&&maxAlpha<1&&minAlpha<maxAlpha))throw Error('Invalid ACI settings');
 const base=buildForecasts(rows,h,{lookback,minCalibration,minHistory});
 const out=[];let alpha=targetMiss,feedbackCount=0;
 for(const r of base){
  const mature=out.filter(p=>!p.feedbackUsed&&p.targetIndex<r.originIndex);
  for(const p of mature){
   p.feedbackUsed=true;
   if(p.covered!==null){
    alpha=clip(alpha+gamma*(targetMiss-(p.covered?0:1)),minAlpha,maxAlpha);
    feedbackCount++;
   }
  }
  const past=base.filter(p=>p.targetIndex<r.originIndex&&p.originIndex<r.originIndex).slice(-lookback);
  const residuals=past.map(p=>Math.abs(p.predictions[r.selected]-p.actual)/p.predictions[r.selected]);
  const band=residuals.length>=minCalibration?Math.max(.002,quantile(residuals,1-alpha)):null;
  const covered=band===null?null:(r.actual>=r.point*(1-band)&&r.actual<=r.point*(1+band));
  out.push({...r,band,covered,alphaAtIssue:alpha,feedbackCountAtIssue:feedbackCount,feedbackUsed:false});
 }
 return out;
}
export function evaluate(arr,{from='2015-01-01',to='2026-09-01'}={}){
 const rows=arr.filter(r=>r.targetMonth>=from&&r.targetMonth<=to&&r.band!==null);
 if(!rows.length)return null;
 const mean=a=>a.reduce((x,y)=>x+y,0)/a.length;
 const scores=rows.map(r=>{
  const lo=r.point*(1-r.band),hi=r.point*(1+r.band);
  return (hi-lo)+10*Math.max(0,lo-r.actual)+10*Math.max(0,r.actual-hi);
 });
 return {n:rows.length,coveragePct:100*mean(rows.map(r=>+r.covered)),meanBandPct:100*mean(rows.map(r=>r.band)),meanWidthUsd:mean(rows.map(r=>2*r.point*r.band)),intervalScoreUsd:mean(scores),misses:rows.filter(r=>!r.covered).length};
}

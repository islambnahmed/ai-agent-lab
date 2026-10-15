/** Offline release-aware evaluator. Retrospective actuals are NOT operationally
 * available until verified publication time. Strict < t avoids same-tick races.
 * No distribution-free time-series coverage guarantee.
 */
import {bandQuantile} from './causal-bands.mjs';
export function publishedBands(rows,{horizon,window=100,minRows=60,coverage=.8,floor=.002,
  guardLookback=50,maxPendingFraction=null}={}){
  if(!Number.isInteger(horizon)||horizon<1||!Number.isInteger(window)||window<1||
     !Number.isInteger(minRows)||minRows<1||minRows>window||
     !Number.isInteger(guardLookback)||guardLookback<1||
     (maxPendingFraction!==null&&(!Number.isFinite(maxPendingFraction)||maxPendingFraction<0||maxPendingFraction>1)))
    throw Error('Invalid settings');
  if(!Array.isArray(rows))throw Error('Rows must be an array');
  let prev=-Infinity;const seen=[],out=[];
  for(const r of rows){
    if(!Number.isInteger(r.originIndex)||r.originIndex<=prev||
       !Number.isFinite(r.point)||r.point<=0||!Number.isFinite(r.actual)||r.actual<=0||
       r.horizon!==horizon||
       !(r.availableAtIndex===Infinity||(Number.isInteger(r.availableAtIndex)&&r.availableAtIndex>=r.originIndex+horizon)))
      throw Error('Invalid forecast, order, or publication timestamp');
    prev=r.originIndex;
    const published=seen.filter(x=>x.availableAtIndex<r.originIndex).slice(-window);
    const matured=seen.filter(x=>x.originIndex+horizon<r.originIndex).slice(-guardLookback);
    const pending=matured.filter(x=>x.availableAtIndex>=r.originIndex).length;
    const pendingFraction=matured.length?pending/matured.length:0;
    const band=published.length>=minRows?bandQuantile(published.map(x=>x.error),coverage,floor):null;
    const emitted=band!==null&&(maxPendingFraction===null||pendingFraction<=maxPendingFraction);
    out.push({originIndex:r.originIndex,band,emitted,
      status:band===null?'insufficient':emitted?'emitted':'pending_guard',
      nPublished:published.length,nMaturedRecent:matured.length,nPendingRecent:pending,
      pendingFraction,covered:emitted?Math.abs(r.point-r.actual)/r.point<=band:null});
    seen.push({originIndex:r.originIndex,availableAtIndex:r.availableAtIndex,
      error:Math.abs(r.point-r.actual)/r.point});
  }
  return out;
}

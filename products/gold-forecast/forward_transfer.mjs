/** Khepri 154 — fixed-model forward transfer test.
 * Requires chronological strictly positive prices. Uses only information
 * available at each origin, and NEVER reselects model on future data.
 * No market data or network I/O.
 */
import {forecast, predict} from './forecast.mjs';

export function scoreFixedModel(trainPrices, futurePrices, horizon, model) {
  if (![1,7,30].includes(horizon)) throw new RangeError('unsupported horizon');
  if (!Array.isArray(trainPrices) || trainPrices.length < 165 || !Array.isArray(futurePrices)) throw new TypeError('invalid series');
  const all=[...trainPrices,...futurePrices];
  if(all.some(p=>!Number.isFinite(p)||p<=0)) throw new TypeError('nonpositive/nonfinite price');
  const differences=[];
  for(let i=trainPrices.length;i+horizon-1<all.length;i++) {
    const hist=all.slice(0,i);
    const actual=all[i+horizon-1];
    const baseline=predict(hist,horizon,'persistence');
    const candidate=predict(hist,horizon,model);
    differences.push({origin:i-1,target:i+horizon-1,
      candidateError:Math.abs(candidate-actual),baselineError:Math.abs(baseline-actual),
      relativeImprovement:(Math.abs(baseline-actual)-Math.abs(candidate-actual))/actual});
  }
  const n=differences.length;
  if(n===0) return {status:'insufficient_future',n:0};
  const avg=k=>differences.reduce((a,r)=>a+r[k],0)/n;
  const candidateMAE=avg('candidateError'),baselineMAE=avg('baselineError');
  const windowGain=(subset)=>{if(!subset.length)return null;const c=subset.reduce((a,r)=>a+r.candidateError,0);const b=subset.reduce((a,r)=>a+r.baselineError,0);return b===0?null:100*(b-c)/b;};
  const early=differences.slice(0,Math.min(30,n)),late=differences.slice(Math.min(30,n));
  return {status:'evaluated',n,nonoverlapUpperBound:Math.ceil(n/horizon),candidateMAE,baselineMAE,
    improvementPct:baselineMAE===0?null:100*(baselineMAE-candidateMAE)/baselineMAE,
    beat: candidateMAE < baselineMAE - 1e-10, earlyN:early.length,earlyImprovementPct:windowGain(early),lateImprovementPct:windowGain(late)};
}
export function auditForwardTransfer(trainPrices, futurePrices, horizon) {
  if(!Array.isArray(trainPrices)||trainPrices.some(p=>!Number.isFinite(p)||p<=0))throw new TypeError('invalid train prices');
  const train=trainPrices.map((price,i)=>({date:new Date(Date.UTC(2020,0,1+i)).toISOString().slice(0,10),price}));
  const chosen=forecast(train,horizon);
  const future=scoreFixedModel(trainPrices,futurePrices,horizon,chosen.model);
  return {horizon,model:chosen.model,auditBeat:chosen.beat,
    auditMAE:chosen.audit.mae,auditBaselineMAE:chosen.baseline.mae,
    auditN:chosen.audit.n, future,transfer:future.status==='evaluated' ? (chosen.beat&&future.beat?'confirmed':chosen.beat&&!future.beat?'failed':!chosen.beat&&future.beat?'unexpected_gain':'no_claim'):null};
}

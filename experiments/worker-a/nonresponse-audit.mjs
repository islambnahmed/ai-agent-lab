/** Worker A cycle 235: two-phase audit nonresponse and imperfect labels.
 * Synthetic evaluation only. No production reliability claims.
 * Node >=18; no external dependencies. */
import {pathToFileURL} from 'node:url';

export function rng(seed) {
  if (!Number.isInteger(seed)) throw Error('seed must be integer');
  let a=seed>>>0;
  return ()=>{a=(a+0x6D2B79F5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296;};
}
export function choose(items,k,random) {
  if(!Number.isInteger(k)||k<0||k>items.length) throw Error('invalid sample size');
  const a=[...items];
  for(let i=0;i<k;i++){const j=i+Math.floor(random()*(a.length-i));[a[i],a[j]]=[a[j],a[i]];}
  return a.slice(0,k);
}
export function correctSymmetricNoise(observedRisk,assumedFlip) {
  if(!(assumedFlip>=0&&assumedFlip<.5)) throw Error('invalid assumed noise');
  return (observedRisk-assumedFlip)/(1-2*assumedFlip); // DO NOT CLIP: clipping breaks unbiasedness.
}
/** Fails closed on incomplete phase-2 audits; no imputation of unavailable labels. */
export function estimateTwoPhase({budget,primaryLosses,missingCount,followupLosses,assumedFlip=0}) {
  if(!Number.isInteger(budget)||budget<1||!Number.isInteger(missingCount)||missingCount<0||missingCount>budget||
      !Array.isArray(primaryLosses)||primaryLosses.length!==budget-missingCount||
      !Array.isArray(followupLosses)||
      (missingCount>0&&followupLosses.length===0)||followupLosses.length>missingCount||
      ![...primaryLosses,...followupLosses].every(x=>x===0||x===1)) throw Error('incomplete or invalid audit');
  const sum=xs=>xs.reduce((a,b)=>a+b,0);
  const raw=(sum(primaryLosses)+(missingCount?missingCount/followupLosses.length*sum(followupLosses):0))/budget;
  return {raw,corrected:correctSymmetricNoise(raw,assumedFlip)};
}
export function ledger(seed,n=540) {
  const r=rng(seed),accepted=[];
  for(let id=0;id<n;id++) {
    const take=r()<.6, proxy=Number(r()<.2), pred=Number(r()<.5);
    const loss=Number(r()<(proxy?.45:.04));
    if(take) accepted.push({id,pred,proxy,loss});
  }
  return accepted;
}
function noisy(loss,mode,r) {
  if(mode==='clean') return loss;
  if(mode==='symmetric') return loss^Number(r()<.08);
  if(mode==='asymmetric') return loss^Number(r()<(loss?.25:.02));
  throw Error('invalid label mode');
}
/** Two-phase design: SRS first; response MNAR; random followup of 50% of nonresponders.
 * Phase-2 labels must be obtainable for EVERY selected followup; otherwise invalid.
 * First-phase response and noisy-label draws depend on hidden truth, but sampling does not.
 * `sampleBounds` applies ONLY to the fixed first-phase sample and ONLY when mode=clean.
 */
export function runOne(seed,{mode='clean',budget=80,assumedFlip=0,followupShare=.5}={}) {
  if(!['clean','symmetric','asymmetric'].includes(mode)||!Number.isInteger(budget)||budget<1||!(followupShare>0&&followupShare<=1)) throw Error('invalid design');
  const population=ledger(seed),N=population.length;
  if(budget>N) throw Error('budget exceeds accepted population');
  const random=rng(seed+900001),sample=choose(population,budget,random);
  const trueRisk=population.reduce((s,x)=>s+x.loss,0)/N;
  let firstSum=0,firstCount=0,cleanFirstSum=0;const primaryLosses=[];
  const missing=[];
  for(const row of sample) {
    // True errors are harder to audit. The response model is NOT assumed known to estimator.
    if(random()<(row.loss?.15:.85)) {
      const label=noisy(row.loss,mode,random);firstSum+=label;primaryLosses.push(label);
      cleanFirstSum+=row.loss;
      firstCount++;
    } else missing.push(row);
  }
  const M=missing.length,k=M?Math.max(1,Math.ceil(M*followupShare)):0;
  const followed=choose(missing,k,random);
  const followupLosses=followed.map(row=>noisy(row.loss,mode,random));
  const observedOnly=firstCount?firstSum/firstCount:null;
  const {raw:rawTwoPhase,corrected}=estimateTwoPhase({budget,primaryLosses,missingCount:M,followupLosses,assumedFlip});
  const sampleTruth=sample.reduce((s,x)=>s+x.loss,0)/budget;
  const sampleBounds=mode==='clean'?[cleanFirstSum/budget,(cleanFirstSum+M)/budget]:null;
  return {N,trueRisk,sampleTruth,observedOnly,rawTwoPhase,corrected,missing:M,followup:k,
    sampleBounds,firstCount};
}
const mean=a=>a.reduce((x,y)=>x+y,0)/a.length;
const round=x=>Number(x.toFixed(5));
function metric(runs,key){
  const diff=runs.map(r=>r[key]-r.trueRisk);
  const bias=mean(diff),mae=mean(diff.map(Math.abs)),rmse=Math.sqrt(mean(diff.map(x=>x*x)));
  const sd=Math.sqrt(diff.reduce((s,x)=>s+(x-bias)**2,0)/(diff.length-1));
  return {meanPct:round(100*mean(runs.map(r=>r[key]))),biasPctPoints:round(100*bias),
    bias95CI:[round(100*(bias-1.96*sd/Math.sqrt(diff.length))),round(100*(bias+1.96*sd/Math.sqrt(diff.length)))],
    maePctPoints:round(100*mae),rmsePctPoints:round(100*rmse)};
}
export function benchmark({trials=1000,seed=83500000,mode='clean',assumedFlip=0}={}) {
  if(!Number.isInteger(trials)||trials<2) throw Error('trials >=2 required');
  const runs=Array.from({length:trials},(_,i)=>runOne(seed+i,{mode,assumedFlip}));
  const base={mode,assumedFlip,trials,seed,
    trueRiskPct:round(100*mean(runs.map(r=>r.trueRisk))),
    averagePrimaryResponsePct:round(100*mean(runs.map(r=>r.firstCount/80))),
    meanFollowupCount:round(mean(runs.map(r=>r.followup))),
    observedOnly:metric(runs,'observedOnly'),
    rawTwoPhase:metric(runs,'rawTwoPhase'),
    corrected:metric(runs,'corrected'),
    idealFullSample:metric(runs,'sampleTruth')};
  if(mode==='clean') base.sampleBoundsCoveragePct=round(100*mean(runs.map(r=>Number(r.sampleBounds[0]<=r.sampleTruth&&r.sampleTruth<=r.sampleBounds[1]))));
  return base;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
  const trials=Number(process.argv[2]??1000),seed=Number(process.argv[3]??83500000);
  console.log(JSON.stringify({clean:benchmark({trials,seed,mode:'clean'}),
    calibrated:benchmark({trials,seed:seed+100000,mode:'symmetric',assumedFlip:.08}),
    miscalibrated:benchmark({trials,seed:seed+200000,mode:'symmetric',assumedFlip:.02}),
    asymmetric:benchmark({trials,seed:seed+300000,mode:'asymmetric',assumedFlip:.08})},null,2));
}

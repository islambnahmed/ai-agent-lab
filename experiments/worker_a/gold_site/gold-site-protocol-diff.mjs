/** Compare historical walk-forward protocols without confusing a sample change with model skill.
 * Offline retrospective audit. The output is not a prospective forecast evaluation.
 */
import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {parsePriceCSV} from './gold-site-offline-eval.mjs';
import {walkForward as v11} from './gold-site-walkforward.mjs';
import {walkForward as v12, DEFAULT_ALPHAS} from './gold-site-walkforward-v1_2.mjs';

const metrics = r => ({
 protocol:r.protocol, scheduled:r.counts.scheduled, evaluated:r.counts.evaluated,
 invalidCandidate:r.counts.invalidCandidate, clippedAnchors:r.counts.clippedAnchors??null,
 scoredMonthly:r.aggregate.n, persistenceMAE:r.aggregate.persistenceMAE,
 selectedMAE:r.aggregate.selectedMAE, momentumMAE:r.aggregate.momentumMAE,
 selectedAlphaByMonth:r.monthly.map(m=>({month:m.month,testN:m.testN,selectedAlpha:m.selectedAlpha}))
});
const changed = (a,b) => a===null||b===null ? a!==b : Math.abs(a-b)>1e-9*Math.max(1,Math.abs(a),Math.abs(b));
const drift = (a,b) => ({
 evaluatedCountDiffers:a.evaluated!==b.evaluated,
 monthlyTestCountsDiffer:a.selectedAlphaByMonth.some((m,i)=>m.testN!==b.selectedAlphaByMonth[i]?.testN),
 baselineMAEDiffers:changed(a.persistenceMAE,b.persistenceMAE),
 // These summaries are NOT a proof that issue timestamps are identical.
 observableSampleDrift:a.evaluated!==b.evaluated||a.selectedAlphaByMonth.some((m,i)=>m.testN!==b.selectedAlphaByMonth[i]?.testN)||changed(a.persistenceMAE,b.persistenceMAE)
});

export function protocolDiff(rows,{alphas=DEFAULT_ALPHAS,controlAlphas=[0,1],...opts}={}){
 if(!Array.isArray(alphas)||!Array.isArray(controlAlphas)||!alphas.includes(0)||!controlAlphas.includes(0)||
    !controlAlphas.every(a=>alphas.includes(a))||controlAlphas.length===alphas.length)throw Error('Control must be a strict candidate subset containing zero');
 const allOpts={...opts,alphas},controlOpts={...opts,alphas:controlAlphas};
 const oldFull=metrics(v11(rows,allOpts));
 const oldControl=metrics(v11(rows,controlOpts));
 const newFull=metrics(v12(rows,allOpts));
 const newControl=metrics(v12(rows,controlOpts));
 return {kind:'retrospective-protocol-and-candidate-set-audit',source:rows[0]?.source??null,
  rows:rows.length,alphas:[...alphas],controlAlphas:[...controlAlphas],
  v11:{full:oldFull,control:oldControl,candidateSetDrift:drift(oldFull,oldControl)},
  v12:{full:newFull,control:newControl,candidateSetDrift:drift(newFull,newControl)},
  protocolChange:{evaluatedDelta:newFull.evaluated-oldFull.evaluated,
   scoredMonthlyDelta:newFull.scoredMonthly-oldFull.scoredMonthly,
   baselineMAEDelta:newFull.persistenceMAE===null||oldFull.persistenceMAE===null?null:newFull.persistenceMAE-oldFull.persistenceMAE},
  caveats:[
   'Summary-level equality cannot prove identical issue timestamps or paired cohorts.',
   'clippedAnchors counts candidate clipping before maturity and target availability checks; not necessarily scored cases.',
   'Different scored cohorts must not be interpreted as improved forecasting skill.',
   'No prospective timestamps, broker execution, or independently verified quote provenance.'
  ]};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 try{
  if(process.argv.length!==3)throw Error('Usage: node gold-site-protocol-diff.mjs quotes.csv');
  const rows=parsePriceCSV(readFileSync(process.argv[2],'utf8'));
  console.log(JSON.stringify(protocolDiff(rows),null,2));
 }catch(e){console.error(e.message);process.exitCode=1;}
}

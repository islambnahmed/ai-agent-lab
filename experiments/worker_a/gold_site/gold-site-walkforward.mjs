/** Retrospective fixed-clock walk-forward XAU/USD comparison.
 * Version 1.1: training outcome must have been OBSERVED before test-month start,
 * not merely targeted before it. No prospective skill claim.
 */
import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {parsePriceCSV} from './gold-site-offline-eval.mjs';

export const MIN=60_000;
export const HORIZON=75*MIN;
export const DEFAULT_ALPHAS=Object.freeze([-1,-0.5,-0.25,-0.1,0,0.1,0.25,0.5,1]);
export const DEFAULT_MONTHS=Object.freeze(['2026-05','2026-06','2026-07','2026-08','2026-09']);
const START=Date.parse('2026-03-27T00:00:00Z');
const END=Date.parse('2026-09-25T20:00:00Z');
const ASOF=Date.parse('2026-09-25T20:45:00Z');
const before=(rows,t)=>{let lo=0,hi=rows.length;while(lo<hi){const m=(lo+hi)>>>1;if(rows[m].t<=t)lo=m+1;else hi=m;}return lo-1;};
const after=(rows,t)=>{let lo=0,hi=rows.length;while(lo<hi){const m=(lo+hi)>>>1;if(rows[m].t<t)lo=m+1;else hi=m;}return lo;};
const loss=(x,a)=>Math.abs(x.actual-(x.base+a*x.trend));
const mean=(xs,fn)=>xs.reduce((sum,x)=>sum+fn(x),0)/xs.length;
const validMonth=s=>typeof s==='string'&&/^\d{4}-(0[1-9]|1[0-2])$/.test(s);

export function walkForward(rows,{startMs=START,endMs=END,asOfMs=ASOF,
 months=DEFAULT_MONTHS,alphas=DEFAULT_ALPHAS}={}){
 if(!Array.isArray(rows)||!rows.length)throw Error('Observations required');
 let prev=-Infinity,source;
 for(const x of rows){if(!x||!Number.isSafeInteger(x.t)||x.t<=prev||!Number.isFinite(x.price)||x.price<=0||
   typeof x.source!=='string'||!x.source||(source!==undefined&&x.source!==source))throw Error('Invalid ordered observations');
   prev=x.t;source=x.source;}
 if(![startMs,endMs,asOfMs].every(Number.isSafeInteger)||endMs<startMs||endMs>asOfMs||
  (endMs-startMs)/HORIZON>100000)throw Error('Invalid grid');
 if(!Array.isArray(months)||!months.length||months.some(m=>!validMonth(m))||
  new Set(months).size!==months.length||months.some((m,i)=>i>0&&m<=months[i-1]))throw Error('Months must be unique and increasing');
 if(!Array.isArray(alphas)||!alphas.includes(0)||alphas.length>40||
  alphas.some(a=>!Number.isFinite(a)||Math.abs(a)>10)||new Set(alphas).size!==alphas.length)throw Error('Invalid candidate alphas');
 const paired=[];const counts={scheduled:0,missingIssue:0,missingLookback:0,invalidCandidate:0,notMatured:0,missingTarget:0,evaluated:0};
 for(let t=startMs;t<=endMs;t+=HORIZON){
  counts.scheduled++;
  const i=before(rows,t);
  if(i<0||t-rows[i].t>2*MIN){counts.missingIssue++;continue;}
  const j=before(rows,t-30*MIN);
  if(j<0||t-30*MIN-rows[j].t>5*MIN){counts.missingLookback++;continue;}
  const target=t+HORIZON;
  const base=rows[i].price;
  const trend=(base-rows[j].price)/(rows[i].t-rows[j].t)*(target-rows[i].t);
  if(!Number.isFinite(trend)||alphas.some(a=>!Number.isFinite(base+a*trend)||base+a*trend<=0)){
   counts.invalidCandidate++;continue;
  }
  if(target>asOfMs){counts.notMatured++;continue;}
  const k=after(rows,target);
  if(k>=rows.length||rows[k].t>target+10*MIN||rows[k].t>asOfMs){counts.missingTarget++;continue;}
  counts.evaluated++;
  paired.push({t,target,observedAt:rows[k].t,base,trend,actual:rows[k].price});
 }
 const result=[];let sumP=0,sumSelected=0,sumMomentum=0,total=0;
 for(const month of months){
  const from=Date.parse(month+'-01T00:00:00Z');
  const to=new Date(from);to.setUTCMonth(to.getUTCMonth()+1);
  // A target before month start is NOT enough: its outcome quote may arrive later.
  const train=paired.filter(x=>x.target<from&&x.observedAt<from);
  const excludedLateTrainingOutcomes=paired.filter(x=>x.target<from&&x.observedAt>=from).length;
  const test=paired.filter(x=>x.t>=from&&x.t<+to);
  if(!train.length||!test.length){result.push({month,trainN:train.length,testN:test.length,excludedLateTrainingOutcomes,selectedAlpha:null,reason:'Insufficient train or test observations'});continue;}
  const candidates=alphas.map(alpha=>({alpha,mae:mean(train,x=>loss(x,alpha))}));
  candidates.sort((a,b)=>a.mae-b.mae||Math.abs(a.alpha)-Math.abs(b.alpha)||a.alpha-b.alpha);
  const selectedAlpha=candidates[0].alpha;
  const p=mean(test,x=>loss(x,0)),s=mean(test,x=>loss(x,selectedAlpha)),m=mean(test,x=>loss(x,1));
  result.push({month,trainN:train.length,testN:test.length,excludedLateTrainingOutcomes,selectedAlpha,
   trainMAE:candidates[0].mae,persistenceMAE:p,selectedMAE:s,momentumMAE:m,
   skillVsPersistence:p>0?1-s/p:null});
  total+=test.length;sumP+=p*test.length;sumSelected+=s*test.length;sumMomentum+=m*test.length;
 }
 return {protocol:'worker-a-fixed-75m-walk-forward-v1.1-causal-outcome-cutoff',source,
  design:'Retrospective; monthly model chosen only from outcomes actually observed before month start',
  alphas:[...alphas],months:[...months],counts,
  aggregate:{n:total,persistenceMAE:total?sumP/total:null,selectedMAE:total?sumSelected/total:null,
   momentumMAE:total?sumMomentum/total:null,skillVsPersistence:sumP>0?1-sumSelected/sumP:null},
  monthly:result,
  warning:'Not a prospective or independently timestamped test. Candidate set and month windows were chosen retrospectively; no trading costs.'};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 try{if(process.argv.length!==3)throw Error('Usage: node gold-site-walkforward.mjs observed.csv');
  const rows=parsePriceCSV(readFileSync(process.argv[2],'utf8'));
  console.log(JSON.stringify(walkForward(rows),null,2));
 }catch(e){console.error(e.message);process.exitCode=1;}
}

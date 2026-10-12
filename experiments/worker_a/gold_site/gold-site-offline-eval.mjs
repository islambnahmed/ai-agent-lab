/** Reproducible offline XAU/USD 75-minute forecast comparison.
 * Never claims live/prospective or independent evidence from imported CSV.
 * No external packages, network, localStorage or broker connections.
 */
import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';

export const HORIZON_MS=75*60_000;
const MIN=60_000;
const MAX_TARGET_LAG=10*MIN;
const LOOKBACK=30*MIN;
const MAX_LOOKBACK_LAG=5*MIN;
const UTC=/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,3})?Z$/;

export function utcMs(s){
 if(typeof s!=='string'||!UTC.test(s))throw Error('Strict UTC timestamp required');
 const ms=Date.parse(s);
 if(!Number.isFinite(ms)||new Date(ms).toISOString().slice(0,19)!==s.slice(0,19))throw Error('Invalid UTC timestamp');
 return ms;
}
export function parsePriceCSV(text){
 if(typeof text!=='string')throw Error('CSV text required');
 const lines=text.trim().split(/\r?\n/);
 if(lines.shift()?.replace(/^\uFEFF/,'')!=='timestamp,price,source')throw Error('CSV header must be timestamp,price,source');
 if(!lines.length)throw Error('No observations');
 let last=-Infinity,source=null;
 return lines.map((line,i)=>{
  const parts=line.split(',');
  if(parts.length!==3)throw Error(`Invalid CSV row ${i+2}`);
  const [timestamp,p,src]=parts;
  if(!/^\d+(?:\.\d+)?$/.test(p)||!src||!/^[-\w.]+$/.test(src))throw Error(`Invalid price/source at row ${i+2}`);
  const t=utcMs(timestamp),price=Number(p);
  if(!Number.isFinite(price)||price<=0||price>1_000_000||t<=last)throw Error(`Nonpositive price, invalid time or non-monotonic timestamps at row ${i+2}`);
  if(source!==null&&source!==src)throw Error('Mixed quote sources are not comparable');
  last=t;source=src;
  return {t,price,source:src};
 });
}
/** First index with timestamp >= t. */
function lowerBound(rows,t){let lo=0,hi=rows.length;while(lo<hi){const m=(lo+hi)>>>1;if(rows[m].t<t)lo=m+1;else hi=m;}return lo;}
function summarize(errors){
 if(!errors.length)return {n:0,mae:null,rmse:null};
 const sum=errors.reduce((a,b)=>a+b,0);
 return {n:errors.length,mae:sum/errors.length,rmse:Math.sqrt(errors.reduce((a,b)=>a+b*b,0)/errors.length)};
}
/** Evaluate only predeclared chronological holdout issuance points.
 * Anchors separated by strideMs. Both methods evaluated on identical outcomes.
 * Momentum uses a past 30m observation and no future data.
 */
export function evaluateSeries(rows,{asOfMs=rows.at(-1)?.t,holdoutStartMs, strideMs=HORIZON_MS}={}){
 if(!Array.isArray(rows)||rows.length<2||!Number.isSafeInteger(asOfMs)||
    !Number.isSafeInteger(strideMs)||strideMs<MIN||
    (holdoutStartMs!==undefined&&!Number.isSafeInteger(holdoutStartMs)))throw Error('Invalid evaluation options');
 const start=holdoutStartMs??(rows[0].t+Math.floor((rows.at(-1).t-rows[0].t)*0.8));
 const pErrors=[],mErrors=[],deltas=[];
 let eligible=0,matured=0,missing=0,notMatured=0,skippedLookback=0,lastIssue=-Infinity;
 for(const row of rows){
  if(row.t<start||row.t>asOfMs||row.t-lastIssue<strideMs)continue;
  // Require an actually observed historical quote within 5m BEFORE the 30m mark.
  const j=lowerBound(rows,row.t-LOOKBACK+1)-1;
  if(j<0||row.t-LOOKBACK-rows[j].t>MAX_LOOKBACK_LAG){skippedLookback++;continue;}
  const trend=(row.price-rows[j].price)/(row.t-rows[j].t)*HORIZON_MS;
  const momentum=row.price+trend;
  if(momentum<=0||!Number.isFinite(momentum)){skippedLookback++;continue;}
  lastIssue=row.t;eligible++;
  const target=row.t+HORIZON_MS;
  if(target>asOfMs){notMatured++;continue;}
  matured++;
  const k=lowerBound(rows,target);
  if(k===rows.length||rows[k].t>target+MAX_TARGET_LAG||rows[k].t>asOfMs){missing++;continue;}
  const p=Math.abs(rows[k].price-row.price),m=Math.abs(rows[k].price-momentum);
  pErrors.push(p);mErrors.push(m);deltas.push(p-m);
 }
 const coverage=matured? (matured-missing)/matured:null;
 const persistence=summarize(pErrors),momentum30=summarize(mErrors);
 const pairedSkill=persistence.mae===null||persistence.mae===0?null:1-momentum30.mae/persistence.mae;
 return {instrument:'XAU/USD',horizonMinutes:75,holdoutStart:new Date(start).toISOString(),
  asOf:new Date(asOfMs).toISOString(),strideMinutes:strideMs/MIN,
  eligible,matured,evaluated:matured-missing,missing,notMatured,skippedLookback,coverage,
  persistence,momentum30,pairedSkillVsPersistence:pairedSkill,
  evidence:'retrospective CSV only; no independent timestamp witness, no proof of live forecasting skill',
  note:'No parameter selection; momentum fixed at 30 minutes. Sample counts are issue points, not independent market regimes.'};
}
function main(){
 const [path,...args]=process.argv.slice(2);
 if(!path||args.length%2)throw Error('Usage: node gold-site-offline-eval.mjs quotes.csv [--stride-minutes N] [--holdout-start ISO] [--as-of ISO]');
 const opts={};
 for(let i=0;i<args.length;i+=2){const [flag,v]=[args[i],args[i+1]];
  if(flag==='--stride-minutes'){
   const n=Number(v);if(!Number.isSafeInteger(n)||n<1)throw Error('Invalid stride');opts.strideMs=n*MIN;
  }else if(flag==='--holdout-start')opts.holdoutStartMs=utcMs(v);
  else if(flag==='--as-of')opts.asOfMs=utcMs(v);
  else throw Error('Unknown option '+flag);
 }
 const rows=parsePriceCSV(readFileSync(path,'utf8'));
 console.log(JSON.stringify(evaluateSeries(rows,opts),null,2));
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){try{main();}catch(e){console.error(e.message);process.exitCode=1;}}

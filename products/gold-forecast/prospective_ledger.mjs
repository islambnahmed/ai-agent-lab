/**
 * Prospective Gold Lab forecast ledger.
 * Self-reported timestamps and hash links are NOT external proof of issue time.
 * Use trusted, separately timestamped commits for credible prospective claims.
 */
import {createHash} from 'node:crypto';
const HORIZONS=new Set([1,7,30]);
const DATE_RE=/^\d{4}-\d{2}-\d{2}$/;
const SHA_RE=/^[a-f0-9]{64}$/;
const TIME_RE=/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z$/;
function fail(m){throw new Error(m)}
function date(v){
  if(typeof v!=='string'||!DATE_RE.test(v))fail('Invalid date');
  const ms=Date.parse(v+'T00:00:00Z');
  if(!Number.isFinite(ms)||new Date(ms).toISOString().slice(0,10)!==v)fail('Invalid calendar date');
  return v;
}
function time(v){
  if(typeof v!=='string'||!TIME_RE.test(v)||!Number.isFinite(Date.parse(v)))fail('Expected UTC timestamp ending in Z');
  if(new Date(Date.parse(v)).toISOString().slice(0,19)!==v.slice(0,19))fail('Invalid timestamp');
  return v;
}
function positive(v,label){if(typeof v!=='number'||!Number.isFinite(v)||v<=0)fail('Invalid '+label);return v}
function name(v,label){if(typeof v!=='string'||!v.trim()||v.length>120)fail('Invalid '+label);return v}
function canonical(v){
  if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';
  if(v&&typeof v==='object')return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
  if(typeof v==='number'&&!Number.isFinite(v))fail('Nonfinite number');
  if(v===undefined)fail('Undefined field');
  return JSON.stringify(v);
}
const sha=v=>createHash('sha256').update(canonical(v)).digest('hex');
function sessionRows(rows,afterDate){
  if(!Array.isArray(rows)||!rows.length)fail('No session observations');
  let last=afterDate??'';
  return rows.map(row=>{
    if(!row||typeof row!=='object')fail('Invalid session row');
    const d=date(row.date),price=positive(row.price,'session price');
    if(d<=last)fail('Sessions must be unique, chronological, and after the origin');
    last=d;
    return {date:d,price};
  });
}
export function fingerprintHistory(sourceId,rows){
  name(sourceId,'source ID');
  return sha({sourceId,observations:sessionRows(rows)});
}
function validateForecast(e){
  if(e.kind!=='forecast'||e.version!==1)fail('Invalid forecast event');
  time(e.recordedAt);date(e.originDate);
  if(e.recordedAt.slice(0,10)<e.originDate)fail('Forecast recorded before origin date');
  if(!HORIZONS.has(e.horizon))fail('Unsupported horizon');
  name(e.sourceId,'source ID');name(e.model,'model');
  positive(e.originPrice,'origin price');positive(e.point,'forecast price');
  positive(e.lower,'lower bound');positive(e.upper,'upper bound');
  if(e.lower>e.point||e.point>e.upper)fail('Invalid interval');
  if(typeof e.historyFingerprint!=='string'||!SHA_RE.test(e.historyFingerprint))fail('Invalid history fingerprint');
}
function validateSettlement(e,forecasts,settled){
  if(e.kind!=='settlement'||e.version!==1)fail('Invalid settlement event');
  time(e.recordedAt);name(e.sourceId,'settlement source ID');
  if(typeof e.forecastHash!=='string'||!SHA_RE.test(e.forecastHash))fail('Invalid forecast reference');
  const f=forecasts.get(e.forecastHash);
  if(!f)fail('Settlement references missing forecast');
  if(settled.has(e.forecastHash))fail('Duplicate settlement');
  if(Date.parse(e.recordedAt)<Date.parse(f.recordedAt))fail('Settlement predates forecast');
  const rows=sessionRows(e.observations,f.originDate);
  // Prevent hindsight: every target observation must be after forecast issue day.
  // Conservatively reject same-UTC-day settlement without trusted close timestamps.
  if(rows[0].date<=f.recordedAt.slice(0,10))fail('Forecast was recorded after the first target session began');
  if(rows.length!==f.horizon)fail('Must supply exactly horizon observed sessions');
  if(e.recordedAt.slice(0,10)<rows.at(-1).date)fail('Settlement recorded before target observation');
  settled.add(e.forecastHash);
}
export function verifyLedger(ledger){
  if(!Array.isArray(ledger))fail('Ledger must be an array');
  const forecasts=new Map(),settled=new Set(),keys=new Set();
  let priorHash=null,priorTime='';
  for(let i=0;i<ledger.length;i++){
    const e=ledger[i];
    if(!e||typeof e!=='object'||Array.isArray(e))fail('Invalid ledger event');
    if(e.seq!==i+1||e.prevHash!==priorHash)fail('Broken sequence/hash chain');
    if(typeof e.hash!=='string'||!SHA_RE.test(e.hash))fail('Invalid event hash');
    const {hash,...payload}=e;
    if(sha(payload)!==hash)fail('Event contents changed after hashing');
    time(e.recordedAt);
    if(Date.parse(e.recordedAt)<Date.parse(priorTime||'1970-01-01T00:00:00Z'))fail('Nonmonotonic recording timestamps');
    if(e.kind==='forecast'){
      validateForecast(e);
      const key=JSON.stringify([e.sourceId,e.model,e.originDate,e.horizon]);
      if(keys.has(key))fail('Duplicate forecast for source/model/origin/horizon');
      keys.add(key);forecasts.set(hash,e);
    }else if(e.kind==='settlement')validateSettlement(e,forecasts,settled);
    else fail('Unknown event kind');
    priorHash=hash;priorTime=e.recordedAt;
  }
  return {events:ledger.length,forecasts:forecasts.size,settlements:settled.size,tip:priorHash};
}
function append(ledger,body){
  const state=verifyLedger(ledger);
  const payload={version:1,seq:ledger.length+1,prevHash:state.tip,...body};
  if(payload.kind==='forecast')validateForecast(payload);
  const next=[...ledger,{...payload,hash:sha(payload)}];
  verifyLedger(next);
  return next;
}
export function appendForecast(ledger,details){
  if(!details||typeof details!=='object')fail('Forecast details required');
  const {recordedAt,originDate,horizon,sourceId,model,originPrice,point,lower,upper,historyFingerprint}=details;
  return append(ledger,{kind:'forecast',recordedAt,originDate,horizon,sourceId,model,originPrice,point,lower,upper,historyFingerprint});
}
export function appendSettlement(ledger,{recordedAt,forecastHash,sourceId,observations}={}){
  const snapshot=sessionRows(observations);
  return append(ledger,{kind:'settlement',recordedAt,forecastHash,sourceId,observations:snapshot});
}
export function scoreLedger(ledger){
  verifyLedger(ledger);
  const forecasts=new Map(ledger.filter(e=>e.kind==='forecast').map(e=>[e.hash,e]));
  const results=ledger.filter(e=>e.kind==='settlement').map(s=>{
    const f=forecasts.get(s.forecastHash),actual=s.observations.at(-1).price;
    return {forecastHash:f.hash,originDate:f.originDate,targetDate:s.observations.at(-1).date,
      horizon:f.horizon,model:f.model,forecastSource:f.sourceId,settlementSource:s.sourceId,
      actual,point:f.point,absError:Math.abs(f.point-actual),baselineAbsError:Math.abs(f.originPrice-actual),
      insideInterval:actual>=f.lower&&actual<=f.upper};
  });
  const byHorizon={};
  for(const h of HORIZONS){
    const rows=results.filter(r=>r.horizon===h).sort((a,b)=>a.originDate.localeCompare(b.originDate));
    let lastTarget='',disjoint=0;
    for(const r of rows)if(r.originDate>=lastTarget){disjoint++;lastTarget=r.targetDate}
    byHorizon[h]={settled:rows.length,nonoverlappingTargets:disjoint,
      mae:rows.length?rows.reduce((s,r)=>s+r.absError,0)/rows.length:null,
      baselineMae:rows.length?rows.reduce((s,r)=>s+r.baselineAbsError,0)/rows.length:null,
      intervalCoveragePct:rows.length?100*rows.filter(r=>r.insideInterval).length/rows.length:null};
  }
  return {results,byHorizon,unsettled:forecasts.size-results.length,
    warning:'Descriptive only. Issue timestamps are self-reported, hash chains can be rehashed, and source/session completeness require independent verification.'};
}

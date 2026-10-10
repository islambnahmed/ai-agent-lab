// Node-only, offline prospective forecast ledger primitives. A digest is an
// integrity fingerprint, NOT proof of when a forecast was published.
import {createHash} from 'node:crypto';

const fields=['schema','issuedAt','originDate','targetDate','horizon','modelId','sourceId','originPrice','predictedPrice'];
const day=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!Number.isNaN(Date.parse(s+'T00:00:00Z'))&&new Date(s+'T00:00:00Z').toISOString().slice(0,10)===s;
const instant=s=>typeof s==='string'&&/(Z|[+-]\d{2}:\d{2})$/.test(s)&&Number.isFinite(Date.parse(s));
const price=n=>typeof n==='number'&&Number.isFinite(n)&&n>0;
const identifier=s=>typeof s==='string'&&/^[a-zA-Z0-9_.-]{1,80}$/.test(s);
function validate(r){
  if(r.schema!=='gold_prospective_v1'||!day(r.originDate)||!day(r.targetDate)||!instant(r.issuedAt)||
     ![1,7,30].includes(r.horizon)||!identifier(r.modelId)||!identifier(r.sourceId)||
     !price(r.originPrice)||!price(r.predictedPrice))throw Error('LEDGER_INVALID_RECORD');
  const issued=Date.parse(r.issuedAt),origin=Date.parse(r.originDate+'T00:00:00Z'),target=Date.parse(r.targetDate+'T00:00:00Z');
  if(!(origin<=issued&&issued<target&&origin<target))throw Error('LEDGER_HINDSIGHT_OR_ORDER');
}
function canonical(r){return Object.fromEntries(fields.map(k=>[k,r[k]]));}
function digest(r){return createHash('sha256').update(JSON.stringify(canonical(r))).digest('hex');}
export function registerForecast(input){
  const record=canonical({schema:'gold_prospective_v1',...input});
  validate(record);
  return Object.freeze({...record,sha256:digest(record)});
}
export function verifyForecast(record){
  if(!record||typeof record!=='object'||Object.keys(record).sort().join('|')!==[...fields,'sha256'].sort().join('|'))
    throw Error('LEDGER_INVALID_KEYS');
  validate(record);
  if(record.sha256!==digest(record))throw Error('LEDGER_TAMPERED');
  return true;
}
export function scoreForecast(record,outcome){
  verifyForecast(record);
  if(!outcome||outcome.date!==record.targetDate||outcome.sourceId!==record.sourceId||
     !price(outcome.close)||!instant(outcome.observedAt))throw Error('LEDGER_INVALID_OUTCOME');
  if(Date.parse(outcome.observedAt)<Date.parse(record.targetDate+'T00:00:00Z')||
     Date.parse(outcome.observedAt)<=Date.parse(record.issuedAt))throw Error('LEDGER_PREMATURE_OUTCOME');
  return {sha256:record.sha256,modelError:Math.abs(record.predictedPrice-outcome.close),
    baselineError:Math.abs(record.originPrice-outcome.close),targetDate:record.targetDate};
}
export function summarizeScores(scores){
  if(!Array.isArray(scores)||scores.length===0)throw Error('LEDGER_EMPTY_SCORES');
  if(new Set(scores.map(s=>s.sha256)).size!==scores.length)throw Error('LEDGER_DUPLICATE_RECORD');
  if(scores.some(s=>!Number.isFinite(s.modelError)||s.modelError<0||!Number.isFinite(s.baselineError)||s.baselineError<0))
    throw Error('LEDGER_INVALID_SCORE');
  const avg=key=>scores.reduce((sum,s)=>sum+s[key],0)/scores.length;
  const modelMae=avg('modelError'),baselineMae=avg('baselineError');
  return {n:scores.length,modelMae,baselineMae,
    improvementPct:baselineMae===0?null:100*(baselineMae-modelMae)/baselineMae,
    note:'Descriptive only: forecast targets may overlap; SHA-256 does not prove publication time.'};
}

// Immutable forecast receipts. Commit receipts before outcomes mature; a hash
// alone detects edits but does not independently prove the issuance time.
import {createHash} from 'node:crypto';
import {forecast} from './forecast.mjs';
import {parseInstant} from './historical-integrity.mjs';
import {prepareHistory} from './data.mjs';
export const hash=value=>createHash('sha256').update(JSON.stringify(value)).digest('hex');

export function issueReceipt(series,h,{issuedAt,source,codeCommit,sourceManifest}){
  const issued=parseInstant(issuedAt,'Issue timestamp');
  if(!/^[0-9a-f]{40}$/.test(codeCommit))throw Error('Pinned Git code commit required');
  if(typeof source!=='string'||!source.trim())throw Error('Source required');
  const fetched=parseInstant(sourceManifest.receivedAt,'Source receipt time');
  if(fetched>issued||issued-fetched>60*60000)throw Error('Use a snapshot fetched before issue and within one hour');
  series=prepareHistory(series,{asOf:issuedAt}).series;
  const result=forecast(series,h,{asOf:issuedAt});
  // Irregular cadence has no defensible target calendar date. If the last
  // completed observation is older than yesterday, the first unobserved close
  // might already have happened before issuance. Fail closed instead of
  // labeling a potentially retrospective forecast as prospective.
  if(result.calendar==='observations'&&result.dataQuality.ageDays>1)
    throw Error('Cannot issue prospective receipt from stale irregular close');
  if(result.targetDate&&result.targetDate<issuedAt.slice(0,10))throw Error('Target date has already passed');
  const record={schemaVersion:1,issuedAt,source,codeCommit,sourceManifest,modelVersion:result.version,
    horizon:h,calendar:result.calendar,originDate:result.latest.date,originClose:result.latest.price,
    historyHash:hash(series),historyLength:series.length,targetDate:result.targetDate,
    model:result.model,point:result.point,lower:result.lower,upper:result.upper,baseline:result.latest.price,
    caveat:'Requires external Git timestamp anchor before target close; not evidence of predictive skill'};
  return {...record,id:hash(record)};
}
export function verifyReceipt(receipt){
  if(!receipt||typeof receipt!=='object')throw Error('Invalid receipt');
  const {id,...payload}=receipt;
  if(id!==hash(payload)||receipt.schemaVersion!==1)throw Error('Receipt integrity mismatch');
  parseInstant(receipt.issuedAt);
  if(![1,7,30].includes(receipt.horizon)||!Number.isInteger(receipt.historyLength)||receipt.historyLength<165)
    throw Error('Invalid receipt metadata');
  return true;
}
export function settleReceipt(receipt,series,{asOf}={}){
  verifyReceipt(receipt);
  if(parseInstant(asOf)<=parseInstant(receipt.issuedAt))throw Error('Settlement must occur after issue');
  series=prepareHistory(series,{asOf}).series;
  const prefix=series.slice(0,receipt.historyLength);
  if(hash(prefix)!==receipt.historyHash)throw Error('Historical vintage revised / prefix missing: quarantine receipt');
  const index=receipt.targetDate?series.findIndex(p=>p.date===receipt.targetDate):receipt.historyLength+receipt.horizon-1;
  if(index>=series.length)return {id:receipt.id,horizon:receipt.horizon,status:'pending',targetDate:receipt.targetDate};
  if(index<0){
    if(series.at(-1)?.date>receipt.targetDate)throw Error('Target close missing: do not shift the target');
    return {id:receipt.id,horizon:receipt.horizon,status:'pending',targetDate:receipt.targetDate};
  }
  const targetDate=series[index].date;
  if(targetDate<receipt.issuedAt.slice(0,10))throw Error('Outcome predates issue');
  if(targetDate>=asOf.slice(0,10))return {id:receipt.id,horizon:receipt.horizon,status:'pending',targetDate};
  if(index!==receipt.historyLength+receipt.horizon-1)throw Error('Horizon / calendar mismatch');
  const actual=series[index].price;
  return {id:receipt.id,horizon:receipt.horizon,status:'matured',targetDate,actual,
    modelAbsError:Math.abs(receipt.point-actual),baselineAbsError:Math.abs(receipt.baseline-actual),
    covered:actual>=receipt.lower&&actual<=receipt.upper};
}

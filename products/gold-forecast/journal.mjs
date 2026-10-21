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
  const issuedUtcDay=new Date(issued).toISOString().slice(0,10);
  if(result.targetDate&&result.targetDate<issuedUtcDay)throw Error('Target date has already passed');
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
  const issuedMs=parseInstant(receipt.issuedAt),asOfMs=parseInstant(asOf);
  if(asOfMs<=issuedMs)throw Error('Settlement must occur after issue');
  const issuedUtcDay=new Date(issuedMs).toISOString().slice(0,10);
  const asOfUtcDay=new Date(asOfMs).toISOString().slice(0,10);
  series=prepareHistory(series,{asOf}).series;
  const prefix=series.slice(0,receipt.historyLength);
  if(hash(prefix)!==receipt.historyHash)throw Error('Historical vintage revised / prefix missing: quarantine receipt');
  const index=receipt.targetDate?series.findIndex(p=>p.date===receipt.targetDate):receipt.historyLength+receipt.horizon-1;
  if(index>=series.length)return {id:receipt.id,horizon:receipt.horizon,status:'pending',targetDate:receipt.targetDate};
  if(index<0){
    if(series.at(-1)?.date>receipt.targetDate)throw Error('Target close missing: do not shift the target');
    return {id:receipt.id,horizon:receipt.horizon,status:'pending',targetDate:receipt.targetDate};
  }
  if(index!==receipt.historyLength+receipt.horizon-1)throw Error('Horizon / calendar mismatch');
  // Daily source dates do not prove intraday close time. Every counted outcome
  // must be strictly after the UTC issuance day, including for irregular cadence.
  const firstCounted=series[receipt.historyLength];
  if(!firstCounted||firstCounted.date<=issuedUtcDay)
    throw Error('Prospective boundary unverified: first counted close is not after UTC issue day');
  const targetDate=series[index].date;
  if(targetDate>=asOfUtcDay)return {id:receipt.id,horizon:receipt.horizon,status:'pending',targetDate};
  const actual=series[index].price;
  return {id:receipt.id,horizon:receipt.horizon,status:'matured',targetDate,actual,
    modelAbsError:Math.abs(receipt.point-actual),baselineAbsError:Math.abs(receipt.baseline-actual),
    covered:actual>=receipt.lower&&actual<=receipt.upper};
}

// Immutable forecast receipts. Commit receipts before outcomes mature; a hash
// alone detects edits but does not independently prove the issuance time.
import {createHash} from 'node:crypto';
import {forecast} from './forecast.mjs';
import {parseInstant} from './historical-integrity.mjs';
import {prepareHistory} from './data.mjs';
export const hash=value=>createHash('sha256').update(JSON.stringify(value)).digest('hex');

// The fetcher preserves the provider's raw digest, but stores normalized JSON.
// Check the digest of the *stored* bytes before issuing receipts so a stale or
// edited history.json cannot be silently attributed to a different fetch.
export function parseVerifiedHistorySnapshot(rawBytes,manifest){
  if(!Buffer.isBuffer(rawBytes))throw Error('History snapshot bytes required');
  if(manifest?.status!=='fetched'||!(/^[0-9a-f]{64}$/.test(manifest.rawSha256))||
     !(/^[0-9a-f]{64}$/.test(manifest.storedSha256)))
    throw Error('History snapshot manifest missing fetched status or SHA-256 digests; re-fetch data');
  const actual=createHash('sha256').update(rawBytes).digest('hex');
  if(actual!==manifest.storedSha256)throw Error('History snapshot / manifest SHA-256 mismatch; re-fetch data');
  return JSON.parse(rawBytes.toString('utf8'));
}

// A rolling provider feed may legitimately lose old dates outside its window,
// but any changed, missing, or inserted date *inside* the overlapping vintage
// is a source revision. Quarantine rather than silently score a mixed vintage.
export function appendVerifiedVintage(frozen,refreshed,originDate){
  const original=new Map(frozen.map(row=>[row.date,row.price]));
  const latest=new Map(refreshed.map(row=>[row.date,row.price]));
  if(!latest.has(originDate))throw Error('Origin missing from refreshed source');
  const firstRefreshed=refreshed[0].date;
  const firstFrozen=frozen[0].date;
  for(const row of frozen){
    if(row.date>=firstRefreshed&&row.date<=originDate&&!latest.has(row.date))
      throw Error('Provider omitted historical vintage: '+row.date);
    if(latest.has(row.date)&&latest.get(row.date)!==row.price)
      throw Error('Provider revised historical vintage: '+row.date);
  }
  for(const row of refreshed){
    if(row.date>=firstFrozen&&row.date<=originDate&&!original.has(row.date))
      throw Error('Provider inserted historical vintage: '+row.date);
  }
  return frozen.concat(refreshed.filter(row=>row.date>originDate));
}

export function issueReceipt(series,h,{issuedAt,source,codeCommit,sourceManifest}){
  const issued=parseInstant(issuedAt,'Issue timestamp');
  if(!/^[0-9a-f]{40}$/.test(codeCommit))throw Error('Pinned Git code commit required');
  if(typeof source!=='string'||!source.trim())throw Error('Source required');
  const fetched=parseInstant(sourceManifest.receivedAt,'Source receipt time');
  if(fetched>issued||issued-fetched>60*60000)throw Error('Use a snapshot fetched before issue and within one hour');
  // The source snapshot cannot contain a completed close from its own UTC day.
  // Gate against the fetch time, not the later issue time: a midnight crossing
  // must not promote a provisional source-day observation into history.
  series=prepareHistory(series,{asOf:sourceManifest.receivedAt}).series;
  const result=forecast(series,h,{asOf:issuedAt});
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
  // Compare UTC calendar days, not the textual day of an offset timestamp.
  // prepareHistory uses the UTC instant, so settlement must use the same clock.
  const asOfUtcDay=new Date(parseInstant(asOf,'Settlement timestamp')).toISOString().slice(0,10);
  if(targetDate>=asOfUtcDay)return {id:receipt.id,horizon:receipt.horizon,status:'pending',targetDate};
  if(index!==receipt.historyLength+receipt.horizon-1)throw Error('Horizon / calendar mismatch');
  const actual=series[index].price;
  return {id:receipt.id,horizon:receipt.horizon,status:'matured',targetDate,actual,
    modelAbsError:Math.abs(receipt.point-actual),baselineAbsError:Math.abs(receipt.baseline-actual),
    covered:actual>=receipt.lower&&actual<=receipt.upper};
}

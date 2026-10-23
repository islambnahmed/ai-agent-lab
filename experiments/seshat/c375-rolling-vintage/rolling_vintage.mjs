/** Rolling-vintage digest diagnostics. Equality of overlap is not source authentication. */
import {createHash} from 'node:crypto';
const SHA=/^[a-f0-9]{64}$/;
export const digest=value=>createHash('sha256').update(JSON.stringify(value)).digest('hex');
function day(value){
  if(typeof value!=='string'||!/^(\d{4})-(\d{2})-(\d{2})$/.test(value))throw Error('Expected UTC YYYY-MM-DD');
  const ms=Date.parse(value+'T00:00:00Z');
  if(!Number.isFinite(ms)||new Date(ms).toISOString().slice(0,10)!==value)throw Error('Invalid UTC date');
  return value;
}
function checkSeries(series){
  if(!Array.isArray(series)||!series.length)throw Error('Nonempty series required');
  let previous='';
  for(const row of series){
    if(!row||typeof row!=='object'||Array.isArray(row))throw Error('Invalid row');
    const d=day(row.date);
    if(d<=previous)throw Error('Dates must be strictly increasing and unique');
    if(typeof row.price!=='number'||!Number.isFinite(row.price)||row.price<=0)throw Error('Invalid positive price');
    previous=d;
  }
  return series;
}
export function createSuffixCommitment(series){
  checkSeries(series);
  const body={schemaVersion:1,originDate:series.at(-1).date,dates:series.map(r=>r.date),
    suffixDigests:series.map((_,i)=>digest(series.slice(i)))};
  return {...body,id:digest(body)};
}
function checkCommitment(commitment){
  if(!commitment||commitment.schemaVersion!==1||!Array.isArray(commitment.dates)||!Array.isArray(commitment.suffixDigests)||
    commitment.dates.length<1||commitment.dates.length!==commitment.suffixDigests.length||
    commitment.originDate!==commitment.dates.at(-1)||commitment.dates.some((d,i)=>{try{day(d);return i>0&&d<=commitment.dates[i-1];}catch{return true;}})||
    commitment.suffixDigests.some(h=>!SHA.test(h)))throw Error('Invalid commitment structure');
  const {id,...body}=commitment;
  if(id!==digest(body))throw Error('Commitment integrity mismatch');
}
export function auditSuffixCommitment(commitment,current,{minOverlap=30}={}){
  checkCommitment(commitment);checkSeries(current);
  if(!Number.isInteger(minOverlap)||minOverlap<1)throw Error('Invalid minOverlap');
  const {dates,originDate,suffixDigests}=commitment;
  const oldStart=dates[0];
  const observed=current.filter(r=>r.date>=oldStart&&r.date<=originDate);
  const after=current.filter(r=>r.date>originDate).length;
  const base={originDate,originalCount:dates.length,observedAfterOrigin:after,
    observedOverlap:observed.length,minOverlap};
  if(!observed.length)return {...base,status:'indeterminate_no_overlap',certified:false};
  const startIndex=dates.indexOf(observed[0].date);
  if(startIndex<0)return {...base,status:'history_dates_changed',certified:false,reason:'new historical date in original span'};
  const expected=dates.slice(startIndex);
  if(observed.length!==expected.length||observed.some((r,i)=>r.date!==expected[i]))
    return {...base,status:'history_dates_changed',certified:false,reason:'missing, inserted or shifted historical dates'};
  if(digest(observed)!==suffixDigests[startIndex])
    return {...base,status:'history_values_changed',certified:false,reason:'same dates but differing observed prices'};
  const prefixLost=startIndex;
  return {...base,status:prefixLost?'overlap_match_prefix_unverifiable':'full_history_match',
    certified:false,verifiedFrom:observed[0].date,verifiedThrough:originDate,
    missingOriginalPrefixRows:prefixLost,sufficientOverlap:observed.length>=minOverlap,
    caveat:'Equality of recorded snapshot overlap is not independent provider authentication or proof of publication timing'};
}
/** Legacy full-series digest cannot distinguish revision from rolling truncation. */
export function auditLegacyFullHash(receipt,current){
  checkSeries(current);
  if(!receipt||!SHA.test(receipt.historyHash)||!Number.isInteger(receipt.historyLength)||receipt.historyLength<1||
     typeof receipt.originDate!=='string')throw Error('Invalid legacy receipt');
  day(receipt.originDate);
  const prefix=current.slice(0,receipt.historyLength);
  const matches=prefix.length===receipt.historyLength&&prefix.at(-1)?.date===receipt.originDate&&digest(prefix)===receipt.historyHash;
  return {status:matches?'full_history_match':'indeterminate_legacy_prefix',certified:false,
    originalCount:receipt.historyLength,originDate:receipt.originDate,
    caveat:matches?'Digest match is not proof of vendor publication time or authenticity':
      'Full digest mismatch alone cannot distinguish revision, rolling truncation, missing rows or changed normalization'};
}

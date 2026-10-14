/**
 * Worker A: conservative prospective gold receipt settlement gate.
 * Consumes already normalized, dated, completed provider closes. Does not
 * authenticate GitHub anchors, vendor snapshots or publication timestamps.
 * Those inputs must be independently verified before any scientific claim.
 */
import {createHash} from 'node:crypto';

const sha = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');
const day = s => {
  if (typeof s !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(s)) throw Error('UTC date required');
  const n = Date.parse(s+'T00:00:00Z');
  if (!Number.isFinite(n) || new Date(n).toISOString().slice(0,10)!==s) throw Error('Invalid UTC date');
  return s;
};
const instant = s => {
  if (typeof s!=='string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z$/.test(s)) throw Error('Explicit UTC timestamp required');
  const n=Date.parse(s);
  if(!Number.isFinite(n)||new Date(n).toISOString().slice(0,19)!==s.slice(0,19)) throw Error('Invalid UTC timestamp');
  return n;
};
const price = n => typeof n==='number'&&Number.isFinite(n)&&n>0;

export function assessProspectiveSettlement(receipt, series, {anchorAt, asOf, targetFirstPublishedAt=null}={}) {
  if(!receipt||typeof receipt!=='object'||Array.isArray(receipt))throw Error('Receipt required');
  const {id,...payload}=receipt;
  if(typeof id!=='string'||sha(payload)!==id)throw Error('Receipt hash mismatch');
  if(receipt.schemaVersion!==1||receipt.calendar!=='observations'||receipt.targetDate!==null||
    ![1,7,30].includes(receipt.horizon)||!Number.isInteger(receipt.historyLength)||receipt.historyLength<165||
    !/^[0-9a-f]{64}$/.test(receipt.historyHash))throw Error('Unsupported receipt contract');
  if(!price(receipt.point)||!price(receipt.baseline)||!price(receipt.originClose))throw Error('Invalid receipt prices');
  const origin=day(receipt.originDate);
  const issued=instant(receipt.issuedAt), anchor=instant(anchorAt), now=instant(asOf);
  if(anchor<issued)throw Error('Anchor predates receipt issue');
  if(now<=anchor)throw Error('Settlement snapshot must be after anchor');
  if(origin>receipt.issuedAt.slice(0,10))throw Error('Origin after issue');
  if(!Array.isArray(series))throw Error('Normalized provider series required');
  let previous='';
  for(const row of series){
    if(!row||typeof row!=='object'||Array.isArray(row)||Object.keys(row).sort().join(',')!=='date,price')
      throw Error('Expected canonical {date,price} rows');
    const d=day(row.date);
    if(d<=previous)throw Error('Duplicate or out-of-order observation');
    if(d>=asOf.slice(0,10))throw Error('Current/future UTC-day close is not completed');
    if(!price(row.price))throw Error('Invalid provider close');
    previous=d;
  }
  if(series.length<receipt.historyLength)throw Error('Historical prefix unavailable');
  const prefix=series.slice(0,receipt.historyLength);
  if(sha(prefix)!==receipt.historyHash)throw Error('Historical prefix mismatch: quarantine');
  if(prefix.at(-1).date!==origin||prefix.at(-1).price!==receipt.originClose||receipt.baseline!==receipt.originClose)
    throw Error('Origin and baseline inconsistent with frozen prefix');
  const targetIndex=receipt.historyLength+receipt.horizon-1;
  const base={receiptId:id,horizon:receipt.horizon,anchorAt,asOf,
    sourceEvidenceStatus:'external_anchor_and_vendor_publication_not_authenticated_by_this_function',
    verifiedPredictiveSkill:false};
  if(targetIndex>=series.length)return {...base,settlementStatus:'pending',prospectiveStatus:'not_evaluable',remainingObservations:targetIndex-series.length+1};
  const target=series[targetIndex];
  if(target.date<=origin)throw Error('Target must follow frozen origin');
  let prospectiveStatus;
  const anchorDay=anchorAt.slice(0,10);
  if(target.date<anchorDay)prospectiveStatus='target_date_before_anchor';
  else if(target.date===anchorDay)prospectiveStatus='same_day_publication_unresolved';
  else prospectiveStatus='later_target_date_conditional';
  if(targetFirstPublishedAt!==null){
    const published=instant(targetFirstPublishedAt);
    if(targetFirstPublishedAt.slice(0,10)<target.date)throw Error('Target publication predates observation date');
    if(published>now)throw Error('Target publication after settlement snapshot');
    if(published<=anchor)prospectiveStatus='target_already_available_at_anchor';
    else if(target.date>=anchorDay)prospectiveStatus='post_anchor_publication_conditional_on_external_authentication';
  }
  const modelAbsError=Math.abs(receipt.point-target.price);
  const baselineAbsError=Math.abs(receipt.baseline-target.price);
  return {...base,settlementStatus:'matured_observation_unverified_provenance',prospectiveStatus,
    targetDate:target.date,actual:target.price,modelAbsError,baselineAbsError,
    errorReductionUsd:baselineAbsError-modelAbsError,
    caution:'One matured outcome is not predictive skill. Caller must independently authenticate receipt presence at anchor, vendor snapshot, and first-publication evidence.'};
}

// Read-only inputs, write-once prospective outcome snapshots.
// A pinned forecast is not proof of the target's source or publication time.
import {createHash} from 'node:crypto';
import {mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {join} from 'node:path';

const sha256 = s => createHash('sha256').update(s).digest('hex');
const isDigest = x => typeof x === 'string' && /^[0-9a-f]{64}$/.test(x);
const isDate = x => typeof x === 'string' && /^\d{4}-\d\d-\d\d$/.test(x) &&
  Number.isFinite(Date.parse(x+'T00:00:00Z')) && new Date(x+'T00:00:00Z').toISOString().slice(0,10) === x;
const parseTime = (x,label) => {
  if(typeof x !== 'string' || !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$/.test(x) || !Number.isFinite(Date.parse(x)))
    throw Error('Invalid '+label);
  return Date.parse(x);
};
const positive = x => typeof x==='number' && Number.isFinite(x) && x>0;

export function makeOutcomeLock(receipt, outcome, {anchorAt, observedAt, manifest}={}) {
  if(!receipt || !isDigest(receipt.id) || ![1,7,30].includes(receipt.horizon) || !isDate(receipt.originDate)) throw Error('Invalid receipt');
  if(outcome?.status!=='matured' || outcome.id!==receipt.id || outcome.horizon!==receipt.horizon) throw Error('Only matching matured outcomes can be locked');
  if(!isDate(outcome.targetDate) || outcome.targetDate<=receipt.originDate) throw Error('Invalid target date');
  if(!positive(outcome.actual) || !Number.isFinite(outcome.modelAbsError) || outcome.modelAbsError<0 || !Number.isFinite(outcome.baselineAbsError) || outcome.baselineAbsError<0 || typeof outcome.covered!=='boolean') throw Error('Invalid outcome metrics');
  if(!positive(receipt.point) || !positive(receipt.baseline) || !positive(receipt.lower) || !positive(receipt.upper) || receipt.lower>receipt.upper) throw Error('Invalid forecast values');
  const eps=1e-8;
  if(Math.abs(Math.abs(receipt.point-outcome.actual)-outcome.modelAbsError)>eps || Math.abs(Math.abs(receipt.baseline-outcome.actual)-outcome.baselineAbsError)>eps || (outcome.actual>=receipt.lower && outcome.actual<=receipt.upper)!==outcome.covered) throw Error('Outcome arithmetic mismatch');
  const issue=parseTime(receipt.issuedAt,'issue time'), anchor=parseTime(anchorAt,'GitHub anchor time'), observed=parseTime(observedAt,'observation time');
  if(anchor<issue || observed<=anchor) throw Error('Invalid chronology');
  const start=Date.parse(outcome.targetDate+'T00:00:00Z');
  if(observed < start+86400000) throw Error('Target UTC day not completed');
  // Refuse same-day cases: an unauthenticated timestamp string is not
  // independent evidence of the provider's actual release time.
  if(anchor>=start) throw Error('Same-day target requires separately authenticated publication evidence');
  if(!manifest || manifest.url!==receipt.sourceManifest?.url || !isDigest(manifest.rawSha256) || manifest.status!=='fetched') throw Error('Same-provider source snapshot evidence required');
  const fetched=parseTime(manifest.receivedAt,'snapshot receipt time');
  if(fetched>observed || fetched<start+86400000) throw Error('Outcome source snapshot timing invalid');
  const evidence={source:receipt.source,sourceUrl:manifest.url,rawSha256:manifest.rawSha256,receivedAt:manifest.receivedAt,anchorAt,observedAt};
  const core={schemaVersion:1,receiptId:receipt.id,horizon:receipt.horizon,targetDate:outcome.targetDate,actual:outcome.actual,modelAbsError:outcome.modelAbsError,baselineAbsError:outcome.baselineAbsError,covered:outcome.covered,evidence};
  return {...core,lockSha256:sha256(JSON.stringify(core))};
}

export function writeOnceOutcome(directory, lock) {
  if(!lock || !isDigest(lock.receiptId) || !isDigest(lock.lockSha256)) throw Error('Invalid lock');
  const {lockSha256,...core}=lock;
  if(sha256(JSON.stringify(core))!==lockSha256) throw Error('Lock integrity mismatch');
  mkdirSync(directory,{recursive:true});
  const filename=join(directory,lock.receiptId+'.json');
  try {
    writeFileSync(filename,JSON.stringify(lock,null,2)+'\n',{flag:'wx'});
    return {status:'first_locked',path:filename};
  } catch(err) {
    if(err.code!=='EEXIST') throw err;
    const old=JSON.parse(readFileSync(filename,'utf8'));
    const {lockSha256:oldSha,...oldCore}=old;
    if(!isDigest(oldSha)||sha256(JSON.stringify(oldCore))!==oldSha) throw Error('Stored outcome lock corrupted');
    const keys=['receiptId','horizon','targetDate','actual','modelAbsError','baselineAbsError','covered'];
    if(keys.some(k=>old[k]!==lock[k])) return {status:'conflicting_revision',path:filename,first:old,attempt:lock};
    return {status:'unchanged',path:filename};
  }
}

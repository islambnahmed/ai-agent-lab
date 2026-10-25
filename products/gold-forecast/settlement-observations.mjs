/**
 * Local first-observation guard for prospective settlement outcomes.
 *
 * A frozen issuance vintage only protects closes through the forecast origin.
 * Without this guard, a provider revision of the *target* close can silently
 * change a previously reported settlement on the next CLI run.
 *
 * This is a local continuity check, NOT an immutable public timestamp anchor,
 * proof of provider authenticity, or permission to report prospective skill.
 */
import fs from 'node:fs';
import path from 'node:path';

const ID=/^[0-9a-f]{64}$/;
const DAY=/^\d{4}-\d{2}-\d{2}$/;
const quarantined=(outcome,reason)=>({id:outcome.id,horizon:outcome.horizon,
  status:'quarantined',error:reason});

export function preserveFirstObservedTarget(outcome,{directory,observedAt,sourceDigest}={}){
  if(!outcome||typeof outcome!=='object'||!ID.test(outcome.id??'')||
      ![1,7,30].includes(outcome.horizon)||
      !['matured','pending','quarantined'].includes(outcome.status))
    throw new TypeError('Invalid settlement outcome');
  if(typeof directory!=='string'||!directory.trim())throw new TypeError('Settlement baseline directory required');
  const filename=path.join(directory,outcome.id+'.json');
  let previous; let exists=false;
  try{previous=JSON.parse(fs.readFileSync(filename,'utf8'));exists=true;}
  catch(error){if(error.code!=='ENOENT')return quarantined(outcome,'Local first-observation record unreadable');}
  if(exists){
    if(!previous||typeof previous!=='object'||Array.isArray(previous)||
        previous.receiptId!==outcome.id||previous.horizon!==outcome.horizon||
        !DAY.test(previous.targetDate??'')||!Number.isFinite(previous.actual)||previous.actual<=0)
      return quarantined(outcome,'Local first-observation record invalid');
    if(outcome.status==='pending')return quarantined(outcome,'Previously observed target is now missing');
    if(outcome.status==='matured'&&
        (previous.targetDate!==outcome.targetDate||previous.actual!==outcome.actual))
      return quarantined(outcome,'Previously observed target date or price revised');
    return {...outcome};
  }
  if(outcome.status!=='matured')return {...outcome};
  if(!DAY.test(outcome.targetDate??'')||!Number.isFinite(outcome.actual)||outcome.actual<=0||
      typeof observedAt!=='string'||!Number.isFinite(Date.parse(observedAt))||
      !/^[0-9a-f]{64}$/.test(sourceDigest??''))
    throw new TypeError('Invalid first-observation metadata');
  fs.mkdirSync(directory,{recursive:true});
  const record={receiptId:outcome.id,horizon:outcome.horizon,targetDate:outcome.targetDate,
    actual:outcome.actual,observedAt,sourceDigest,
    caveat:'Local first-observation only; not independently timestamped or tamper-proof'};
  try{fs.writeFileSync(filename,JSON.stringify(record,null,2)+'\n',{flag:'wx'});}
  catch(error){
    if(error.code!=='EEXIST')throw error;
    // Never overwrite or retry indefinitely if a competing process wrote it.
    return quarantined(outcome,'Concurrent first-observation record creation; retry later');
  }
  return {...outcome};
}

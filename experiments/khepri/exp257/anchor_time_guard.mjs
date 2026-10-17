/** Khepri exp257: conservative external receipt-anchor timing triage.
 * This is a decision aid, not a cryptographic proof of GitHub server events.
 * Caller MUST independently verify the provider event, its receipt path/blob
 * and server-observed time. User-controlled Git author/committer dates are NOT anchors.
 */
import {createHash} from 'node:crypto';
const DATE=/^\d{4}-\d{2}-\d{2}$/;
const SHA=/^[0-9a-f]{40}$/;
const INSTANT=/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,3})?)?(?:Z|[+-]\d{2}:\d{2})$/;
function dateMs(date){
  if(typeof date!=='string'||!DATE.test(date))throw Error('Invalid target date');
  const ms=Date.parse(date+'T00:00:00Z');
  if(!Number.isFinite(ms)||new Date(ms).toISOString().slice(0,10)!==date)throw Error('Nonexistent target date');
  return ms;
}
function instantMs(value){
  if(typeof value!=='string'||!INSTANT.test(value))throw Error('Explicit zoned timestamp required');
  const ms=Date.parse(value);
  if(!Number.isFinite(ms)||!/^\d{4}-\d{2}-\d{2}$/.test(new Date(ms).toISOString().slice(0,10)))throw Error('Invalid timestamp');
  const [,hh,mm,ss='0']=value.slice(11).match(/^(\d{2}):(\d{2})(?::(\d{2}))?/)??[];
  if(!hh||+hh>23||+mm>59||+ss>59)throw Error('Invalid clock');
  const offset=value.match(/([+-])(\d{2}):(\d{2})$/);
  if(offset&&(+offset[2]>14||+offset[3]>59||(+offset[2]===14&&+offset[3]!==0)))throw Error('Invalid timezone offset');
  return ms;
}
export const gitBlobSha = bytes=>{
  const b=Buffer.isBuffer(bytes)?bytes:Buffer.from(bytes);
  return createHash('sha1').update(Buffer.from(`blob ${b.length}\0`)).update(b).digest('hex');
};
/** Caller supplies externally verified server event. The boolean below is a
 * declaration by that caller; this module cannot authenticate a remote event.
 */
export function auditAnchor({receiptBytes,receiptId,receiptPath,targetDate=null,targetObservedAt=null,events=[]}){
  if(typeof receiptId!=='string'||!/^[0-9a-f]{64}$/.test(receiptId))throw Error('Invalid receipt id');
  if(typeof receiptPath!=='string'||!receiptPath.startsWith('products/gold-forecast/reports/prospective/'))throw Error('Receipt path outside expected lab area');
  const blobSha=gitBlobSha(receiptBytes);
  let deadline;
  if(targetDate!==null)deadline=dateMs(targetDate);
  else if(targetObservedAt!==null)deadline=instantMs(targetObservedAt);
  else return {status:'unanchorable_without_target_observation',blobSha,reason:'Observation-count horizon lacks a calendar target; require independently observed outcome time'};
  const accepted=[],rejected=[];
  for(const e of events){
    if(!e||typeof e!=='object'){rejected.push('invalid_event');continue;}
    if(e.kind!=='server_observation'){rejected.push('untrusted_commit_date');continue;}
    if(!SHA.test(e.commitSha??'')||e.receiptId!==receiptId||e.receiptPath!==receiptPath||e.blobSha!==blobSha){rejected.push('content_or_identity_mismatch');continue;}
    let seen;
    try{seen=instantMs(e.serverObservedAt)}catch{rejected.push('invalid_server_time');continue;}
    if(seen>=deadline){rejected.push('too_late');continue;}
    if(e.independentlyVerified!==true){rejected.push('unverified_server_observation');continue;}
    accepted.push({commitSha:e.commitSha,serverObservedAt:e.serverObservedAt});
  }
  return {status:accepted.length?'conditionally_pre_target':'insufficient_anchor_evidence',blobSha,accepted,rejected,
    caveat:'This tool does not authenticate the provider event. Independent verification of GitHub server event, commit contents and timestamps is required; commit author/committer dates are insufficient.'};
}

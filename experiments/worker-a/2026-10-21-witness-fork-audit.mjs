/**
 * Research-only audit of multiple independently authenticated ledger checkpoints.
 * This does NOT authenticate witnesses, prove real time, detect hidden forks,
 * establish upstream completeness, or verify market prices.
 */
import {buildLedger} from './anchored-history.mjs';
const ISO=/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$/;
const SHA=/^[0-9a-f]{64}$/;
function timestamp(s) {
  if(typeof s!=='string'||!ISO.test(s)||!Number.isFinite(Date.parse(s))) throw Error('Invalid timestamp');
  return Date.parse(s);
}
function fail(reason,detail={}) {return {status:'insufficient_evidence',reason,...detail};}
/** All supplied views must refer to the SAME stream. trustedCheckpointLookup
 * must independently authenticate and origin-freeze every returned checkpoint.
 * Neither assumption can be established inside this function.
 */
export function auditWitnessForks(snapshots,{originAt,trustedCheckpointLookup}={}) {
  const origin=timestamp(originAt);
  if(!Array.isArray(snapshots)||snapshots.length<2||typeof trustedCheckpointLookup!=='function')
    throw Error('At least two independently witnessed snapshots required');
  const ids=snapshots.map(x=>x?.anchorId);
  if(ids.some(id=>typeof id!=='string'||!id.trim())||new Set(ids).size!==ids.length)
    return fail('duplicate_or_invalid_anchor_id');
  const views=[];
  for(const item of snapshots) {
    const id=item.anchorId, cp=trustedCheckpointLookup(id);
    if(!cp||cp.anchorId!==id||!Number.isSafeInteger(cp.count)||cp.count<1||!SHA.test(cp.head??''))
      return fail('invalid_or_untrusted_checkpoint',{anchorId:id});
    if(timestamp(cp.observedAt)>origin)return fail('checkpoint_after_origin',{anchorId:id});
    if(!Array.isArray(item.entries)||item.entries.length<cp.count)
      return fail('missing_committed_prefix',{anchorId:id});
    let rebuilt;
    try{rebuilt=buildLedger(item.entries.slice(0,cp.count).map(e=>e?.record));}
    catch{return fail('invalid_ledger_entries',{anchorId:id});}
    if(rebuilt.some((e,i)=>item.entries[i]?.seq!==e.seq||
       item.entries[i]?.prev!==e.prev||
       item.entries[i]?.payloadSha256!==e.payloadSha256||
       item.entries[i]?.head!==e.head))
      return fail('tampered_ledger_prefix',{anchorId:id});
    if(rebuilt.at(-1).head!==cp.head)return fail('checkpoint_head_mismatch',{anchorId:id});
    if(new Set(rebuilt.map(e=>e.record.receiptId)).size!==rebuilt.length)
      return fail('duplicate_receipt_id',{anchorId:id});
    views.push({anchorId:id,count:cp.count,heads:rebuilt.map(e=>e.head)});
  }
  for(let i=0;i<views.length;i++)for(let j=i+1;j<views.length;j++){
    const a=views[i],b=views[j],common=Math.min(a.count,b.count);
    for(let k=0;k<common;k++)if(a.heads[k]!==b.heads[k])
      return {status:'fork_detected',reason:'divergent_witnessed_prefix',
        firstConflictSeq:k+1,anchorIds:[a.anchorId,b.anchorId],observedSnapshots:views.length};
  }
  return {status:'consistent_observed_prefixes',
    reason:'no_fork_in_supplied_authenticated_views',
    observedSnapshots:views.length,
    highestWitnessedCount:Math.max(...views.map(x=>x.count))};
}

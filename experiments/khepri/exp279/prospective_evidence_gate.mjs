/** Khepri exp279: conditional chronology gate; NOT a verifier of attestations. */
const ISO=/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,3})?)?(?:Z|[+-]\d{2}:\d{2})$/;
function instant(value,name){
  if(typeof value!=='string'||!ISO.test(value))throw Error(name+': timezone-qualified ISO timestamp required');
  const d=value.slice(0,10);
  if(new Date(d+'T00:00:00Z').toISOString().slice(0,10)!==d)throw Error(name+': invalid date');
  const match=value.slice(11).match(/^(\d{2}):(\d{2})(?::(\d{2}))?/);
  if(+match[1]>23||+match[2]>59||+(match[3]??0)>59)throw Error(name+': invalid time');
  const off=value.match(/([+-])(\d{2}):(\d{2})$/);
  if(off&&(+off[2]>14||+off[3]>59||(+off[2]===14&&+off[3]!==0)))throw Error(name+': invalid offset');
  const ms=Date.parse(value);
  if(!Number.isFinite(ms))throw Error(name+': invalid timestamp');
  return ms;
}
const refuse=(reason,status='not_scoreable')=>({status,reason});
/** Caller assertions of verified evidence must be independently checked elsewhere.
 * Git author/committer dates are not independent first-seen timestamps.
 * 'conditionally_eligible' is not a certificate of predictive skill.
 */
export function assessProspectiveEvidence(e){
  if(!e||typeof e!=='object')return refuse('missing_evidence');
  try{
    if(!e.receiptId||typeof e.receiptId!=='string')return refuse('missing_receipt_id');
    if(!e.historyVintageVerified)return refuse('history_vintage_unverified');
    if(!e.targetObservationAt)return refuse('target_observation_time_unknown');
    if(!e.targetPublishedAt)return refuse('target_publication_time_unknown');
    if(!e.anchorEvidence?.observedAt)return refuse('anchor_first_seen_time_unknown');
    if(e.anchorEvidence?.kind!=='independent_first_seen'||e.anchorEvidence?.verified!==true)
      return refuse('anchor_not_independently_attested');
    if(e.anchorEvidence?.receiptId!==e.receiptId)return refuse('anchor_receipt_mismatch');
    const issue=instant(e.issuedAt,'issuedAt');
    const history=instant(e.historySnapshotReceivedAt,'historySnapshotReceivedAt');
    const anchor=instant(e.anchorEvidence.observedAt,'anchorObservedAt');
    const close=instant(e.targetObservationAt,'targetObservationAt');
    const publication=instant(e.targetPublishedAt,'targetPublishedAt');
    const settlement=instant(e.settlementAsOf,'settlementAsOf');
    if(history>issue)return refuse('history_snapshot_after_issue');
    if(issue-history>3600000)return refuse('history_snapshot_stale');
    if(anchor<issue)return refuse('anchor_predates_issue');
    if(issue>=close)return refuse('forecast_not_before_target_observation');
    if(anchor>=close)return refuse('anchor_not_before_target_observation');
    if(publication<close)return refuse('target_publication_predates_observation');
    if(settlement<publication)return refuse('target_not_yet_published','pending');
    return {status:'conditionally_eligible',reason:'chronology_passes_given_independently_verified_attestations',
      sameUtcDay:new Date(issue).toISOString().slice(0,10)===new Date(close).toISOString().slice(0,10),
      leadMinutes:(close-anchor)/60000};
  }catch(err){return refuse('invalid_evidence: '+err.message);}
}

/** Conservative forward-only UTC date gate. At most one observation per UTC date. */
function utcDay(s,label) {
  if (typeof s !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(s)) throw new TypeError(label+': YYYY-MM-DD required');
  const t=Date.parse(s+'T00:00:00Z');
  if (!Number.isFinite(t)||new Date(t).toISOString().slice(0,10)!==s) throw new RangeError(label+': invalid date');
  return t;
}
export function prospectiveEligibility({originDate,issuedAt,horizon}) {
  if (!Number.isInteger(horizon)||horizon<1||horizon>365) throw new RangeError('invalid horizon');
  if (typeof issuedAt!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z$/.test(issuedAt)||!Number.isFinite(Date.parse(issuedAt)))
    throw new TypeError('issuedAt must be a valid UTC timestamp');
  const originMs=utcDay(originDate,'originDate');
  const issueDay=issuedAt.slice(0,10),issueMs=utcDay(issueDay,'issueDay');
  if(originMs>issueMs)throw new RangeError('origin is in the future');
  const earliestTargetDate=new Date(originMs+horizon*86400000).toISOString().slice(0,10);
  const eligible=earliestTargetDate>issueDay;
  return {eligible,originDate,issueDay,horizon,earliestTargetDate,
    reason:eligible?'earliest_possible_target_after_issue_utc_day':'target_could_already_have_occurred',
    assumption:'at most one provider observation per UTC date',
    caveat:'Eligibility does not establish source-vintage integrity, publication time, or forecast skill'};
}

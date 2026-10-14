/**
 * Conservative timing screen for observation-count gold forecast receipts.
 * This is NOT a settlement engine, signature verification, or proof of vendor
 * publication timing. It only establishes whether the earliest possible
 * target date is strictly later than an independently verified anchor day.
 *
 * Date-level evidence alone cannot establish same-day issue/target order.
 * Future provider observations must be unique, strictly increasing UTC dates.
 */
const DAY = 86400000;
function utcDay(s) {
  if (typeof s !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(s)) throw new TypeError('UTC YYYY-MM-DD required');
  const ms = Date.parse(s + 'T00:00:00.000Z');
  if (!Number.isFinite(ms) || new Date(ms).toISOString().slice(0, 10) !== s) throw new TypeError('Nonexistent UTC date');
  return ms;
}
function utcInstant(s) {
  if (typeof s !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z$/.test(s))
    throw new TypeError('Explicit UTC timestamp required');
  const ms = Date.parse(s);
  if (!Number.isFinite(ms) || new Date(ms).toISOString().slice(0, 19) !== s.slice(0, 19))
    throw new TypeError('Invalid UTC timestamp');
  return ms;
}
const dayString = ms => new Date(ms).toISOString().slice(0, 10);

export function auditProspectiveTiming(receipt, {anchorAt, candidateTargetDate = null} = {}) {
  if (!receipt || receipt.calendar !== 'observations' || receipt.targetDate !== null ||
      !Number.isInteger(receipt.horizon) || receipt.horizon < 1 || receipt.horizon > 365)
    throw new TypeError('Observation-count receipt required');
  const origin = utcDay(receipt.originDate);
  const issued = utcInstant(receipt.issuedAt);
  if (origin > Date.parse(dayString(issued) + 'T00:00:00.000Z'))
    throw new RangeError('Origin cannot be after issue UTC date');
  const earliest = dayString(origin + receipt.horizon * DAY);
  const target = candidateTargetDate === null ? null : dayString(utcDay(candidateTargetDate));
  if (target && utcDay(target) < utcDay(earliest))
    throw new RangeError('Candidate target predates minimum possible unique-date horizon');
  if (anchorAt === undefined || anchorAt === null) return {
    status: 'missing_external_anchor', horizon: receipt.horizon,
    earliestPossibleTargetDate: earliest, candidateTargetDate: target,
    caveat: 'No independently verified issuance anchor supplied.'
  };
  const anchor = utcInstant(anchorAt);
  if (anchor < issued) throw new RangeError('External anchor cannot precede receipt issuedAt');
  const anchorDay = dayString(anchor);
  const examinedDate = target ?? earliest;
  const status = examinedDate < anchorDay ? 'target_date_before_anchor' :
    examinedDate === anchorDay ? 'same_day_timing_unresolved' : 'date_separated_conditional';
  return {
    status, horizon: receipt.horizon, anchorAt, anchorDate: anchorDay,
    earliestPossibleTargetDate: earliest, candidateTargetDate: target,
    caveat: status === 'date_separated_conditional'
      ? 'Target date is later than anchor UTC date under unique-date observation semantics; still verify receipt hash, source vintage, actual target and close convention.'
      : status === 'same_day_timing_unresolved'
        ? 'A UTC date cannot establish whether the target close became available before or after the external anchor. Quarantine until independently evidenced.'
        : 'Target date is earlier than external anchor day; not prospectively eligible.'
  };
}

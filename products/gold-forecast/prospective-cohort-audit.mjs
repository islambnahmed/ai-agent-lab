/**
 * Read-only pre-settlement audit for published prospective forecast cohorts.
 * No provider observations are fetched and no predictive skill is inferred.
 * An anchor timestamp supplied by a caller is NOT independently authenticated
 * by this function. Verify its GitHub provenance outside this module.
 */
import {createHash} from 'node:crypto';

const DAY_MS = 86_400_000;
function dayMs(date) {
  if (typeof date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(date)) throw new TypeError('UTC date YYYY-MM-DD required');
  const ms = Date.parse(date + 'T00:00:00.000Z');
  if (!Number.isFinite(ms) || new Date(ms).toISOString().slice(0, 10) !== date) throw new TypeError('Invalid UTC date');
  return ms;
}
function instantMs(instant) {
  if (typeof instant !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z$/.test(instant))
    throw new TypeError('Explicit UTC timestamp required');
  const ms = Date.parse(instant);
  if (!Number.isFinite(ms) || new Date(ms).toISOString().slice(0, 19) !== instant.slice(0, 19))
    throw new TypeError('Invalid UTC timestamp');
  return ms;
}
const isoDay = ms => new Date(ms).toISOString().slice(0, 10);
const digest = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');

function validateReceipt(r) {
  if (!r || typeof r !== 'object' || Array.isArray(r)) throw new TypeError('Receipt object required');
  const {id, ...payload} = r;
  if (typeof id !== 'string' || id !== digest(payload)) throw new Error('Receipt SHA-256 integrity mismatch');
  if (r.schemaVersion !== 1 || ![1, 7, 30].includes(r.horizon) ||
      r.calendar !== 'observations' || r.targetDate !== null ||
      !Number.isInteger(r.historyLength) || r.historyLength < 165 ||
      !Number.isFinite(r.originClose) || r.originClose <= 0 ||
      !/^[0-9a-f]{64}$/.test(r.historyHash) ||
      !/^[0-9a-f]{40}$/.test(r.codeCommit)) throw new TypeError('Unsupported or invalid receipt contract');
  const origin = dayMs(r.originDate);
  const issued = instantMs(r.issuedAt);
  if (origin > dayMs(isoDay(issued))) throw new Error('Origin later than issue date');
  const manifest = r.sourceManifest;
  if (!manifest || !/^[0-9a-f]{64}$/.test(manifest.rawSha256) ||
      typeof manifest.url !== 'string' || !manifest.url ||
      instantMs(manifest.receivedAt) > issued) throw new TypeError('Invalid source manifest');
  if (typeof r.source !== 'string' || !r.source.trim()) throw new TypeError('Missing source');
  return {origin, issued};
}

export function auditProspectiveCohort(receipts, {anchorAt = null, asOf} = {}) {
  if (!Array.isArray(receipts) || !receipts.length) throw new TypeError('Nonempty receipt cohort required');
  const now = instantMs(asOf);
  const seen = new Set();
  const validated = receipts.map(r => {
    const dates = validateReceipt(r);
    if (seen.has(r.horizon)) throw new Error('Duplicate horizon in same cohort');
    seen.add(r.horizon);
    if (dates.issued > now) throw new Error('Receipt issued in future relative to audit');
    return {receipt:r, ...dates};
  });
  const first = validated[0].receipt;
  const commonFields = ['issuedAt', 'originDate', 'originClose', 'historyHash', 'historyLength', 'source', 'codeCommit'];
  for (const {receipt:r} of validated.slice(1)) {
    if (commonFields.some(key => r[key] !== first[key]) ||
        r.sourceManifest.rawSha256 !== first.sourceManifest.rawSha256 ||
        r.sourceManifest.receivedAt !== first.sourceManifest.receivedAt)
      throw new Error('Mixed origins or vintages: audit as separate cohorts');
  }
  const anchor = anchorAt === null ? null : instantMs(anchorAt);
  if (anchor !== null && (anchor < validated[0].issued || anchor > now))
    throw new Error('External anchor must be between issue and audit time');
  const rows = validated.map(({receipt:r,origin}) => {
    const earliest = isoDay(origin + r.horizon * DAY_MS);
    const anchorDay = anchor === null ? null : isoDay(anchor);
    const timing = anchor === null ? 'missing_external_anchor' :
      earliest < anchorDay ? 'earliest_target_precedes_anchor' :
      earliest === anchorDay ? 'same_day_publication_unresolved' :
      'date_separated_conditional';
    return {
      horizon:r.horizon, receiptId:r.id, earliestPossibleTargetDate:earliest,
      earliestDateReached:dayMs(earliest) <= dayMs(isoDay(now)),
      timingStatus:timing, outcomeStatus:'not_checked_no_provider_rows_supplied',
      scoringStatus:'not_computed'
    };
  }).sort((a,b)=>a.horizon-b.horizon);
  return {
    cohortOriginDate:first.originDate, issuedAt:first.issuedAt, source:first.source,
    anchorAt:anchorAt, receiptCount:rows.length, independentForecastOrigins:1,
    horizons:rows,
    caveat:'A valid receipt hash is not an external timestamp. This read-only screen cannot verify GitHub anchor provenance, source completeness, target publication time, or predictive accuracy.'
  };
}

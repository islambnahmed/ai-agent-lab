/**
 * Conservative audit of future-observation horizons for a prospective receipt.
 * This does NOT authenticate provider prices or substitute for settleReceipt.
 * A gap is indeterminate, not proof that a close is missing: weekends, holidays,
 * and genuine provider outages can all cause gaps.
 *
 * Feed only completed, provider-validated future daily rows. The caller must
 * verify the immutable receipt, original history vintage, source and timestamp.
 */
const DAY_MS = 86_400_000;
function dayMs(date) {
  if (typeof date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(date)) throw new TypeError('ISO UTC date required');
  const ms = Date.parse(date + 'T00:00:00Z');
  if (!Number.isFinite(ms) || new Date(ms).toISOString().slice(0, 10) !== date) throw new TypeError('Invalid UTC date');
  return ms;
}
function dateAt(ms) { return new Date(ms).toISOString().slice(0, 10); }

export function auditObservedCloseSequence(receipt, futureRows) {
  if (!receipt || receipt.calendar !== 'observations' || receipt.targetDate !== null ||
      !Number.isInteger(receipt.horizon) || receipt.horizon < 1 || receipt.horizon > 365 ||
      typeof receipt.originDate !== 'string') throw new TypeError('Observation-horizon receipt required');
  if (!Array.isArray(futureRows)) throw new TypeError('Future rows must be an array');
  const origin = dayMs(receipt.originDate);
  let previous = origin;
  const gaps = [];
  for (let i = 0; i < futureRows.length; i++) {
    const row = futureRows[i];
    if (!row || !Number.isFinite(row.price) || row.price <= 0) throw new TypeError('Validated positive future close required');
    const current = dayMs(row.date);
    if (current <= previous) throw new RangeError('Future dates must strictly increase after origin');
    const days = (current - previous) / DAY_MS;
    if (days > 1) {
      const missing = [];
      for (let d = previous + DAY_MS; d < current; d += DAY_MS) missing.push(dateAt(d));
      gaps.push({after: dateAt(previous), before: row.date, missingDates: missing});
    }
    previous = current;
  }
  const observed = Math.min(receipt.horizon, futureRows.length);
  const candidate = futureRows[receipt.horizon - 1];
  if (gaps.some(g => dayMs(g.before) <= (candidate ? dayMs(candidate.date) : previous))) {
    return {status: 'needs_gap_evidence', horizon: receipt.horizon, observed,
      candidateTargetDate: candidate?.date ?? null, gaps,
      reason: 'Cannot distinguish legitimate market closure from missing provider close without independent evidence'};
  }
  if (!candidate) return {status: 'pending', horizon: receipt.horizon, observed,
    candidateTargetDate: null, gaps: [], reason: 'Fewer than h completed future closes'};
  return {status: 'sequence_contiguous', horizon: receipt.horizon, observed,
    candidateTargetDate: candidate.date, gaps: [],
    reason: 'No calendar-day gap in observed prefix; source integrity and issue-time anchor still require separate verification'};
}

/** Optional adapter: first invoke the canonical settler (which validates the
 * receipt and history hash), then hold an otherwise matured observation-horizon
 * outcome if an unverified gap precedes the candidate target. Never call this
 * adapter on raw/unvalidated provider rows. */
export function settleWithSequenceGuard(receipt, validatedSeries, options, settleReceipt) {
  if (typeof settleReceipt !== 'function') throw new TypeError('Canonical settlement function required');
  const result = settleReceipt(receipt, validatedSeries, options);
  if (result.status !== 'matured' || receipt.calendar !== 'observations') return result;
  const audit = auditObservedCloseSequence(receipt, validatedSeries.slice(receipt.historyLength));
  if (audit.status !== 'sequence_contiguous') return {
    id: receipt.id, horizon: receipt.horizon, status: 'needs_gap_evidence',
    candidateTargetDate: audit.candidateTargetDate, gaps: audit.gaps,
    reason: audit.reason
  };
  return {...result, sequenceAudit: audit};
}

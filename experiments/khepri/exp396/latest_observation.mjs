/**
 * EXP396: A point-in-time *latest observation* selector.
 * Unlike exp395's snapshot(), receipt order is not observation chronology.
 * Caller supplies a trusted exp395 ledger, not arbitrary historical revisions.
 * Trust/authenticity of receivedAt is an external assumption (not solved here).
 */
export function latestObservation(ledger, series, decisionAt, {maxAge = Infinity} = {}) {
  if (!ledger || typeof ledger.receipts !== 'function' ||
      typeof series !== 'string' || !series.trim() ||
      !Number.isSafeInteger(decisionAt) ||
      (maxAge !== Infinity && (!Number.isSafeInteger(maxAge) || maxAge < 0))) {
    throw Error('Invalid latest-observation query');
  }
  const eligible = ledger.receipts().filter(e =>
    e.series === series &&
    Number.isSafeInteger(e.receivedAt) && e.receivedAt <= decisionAt &&
    Number.isSafeInteger(e.effectiveAt) && e.effectiveAt <= decisionAt &&
    decisionAt - e.effectiveAt <= maxAge
  );
  if (!eligible.length) return {status: 'abstain', reason: 'not_available_as_of_decision'};
  // First choose the newest *observation time*. Within that time, use the
  // latest received vintage; revision is only a deterministic secondary tie.
  eligible.sort((a, b) =>
    b.effectiveAt - a.effectiveAt || b.receivedAt - a.receivedAt ||
    b.revision - a.revision || a.id.localeCompare(b.id));
  const w = eligible[0];
  return {status:'available', id:w.id, value:w.value,
          receivedAt:w.receivedAt, effectiveAt:w.effectiveAt};
}

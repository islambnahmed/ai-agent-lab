/** Point-in-time selection from an append-only trusted receipt ledger.
 * This does not authenticate a source, its values, or its timestamp fields.
 */
export function makeLedger() {
  const events = [];
  const ids = new Set();
  let lastReceipt = -Infinity;
  return {
    append(event, trustedReceivedAt) {
      if (!event || typeof event.id !== 'string' || !event.id.trim() || ids.has(event.id) ||
          typeof event.series !== 'string' || !event.series.trim() ||
          !Number.isInteger(event.revision) || event.revision < 0 ||
          !Number.isFinite(event.value) || event.value <= 0 ||
          !Number.isSafeInteger(event.effectiveAt) || !Number.isSafeInteger(event.providerPublishedAt) ||
          !Number.isSafeInteger(trustedReceivedAt) || trustedReceivedAt < lastReceipt) {
        throw Error('Invalid or nonmonotonic receipt');
      }
      const receipt = Object.freeze({ ...event, receivedAt: trustedReceivedAt });
      events.push(receipt); ids.add(event.id); lastReceipt = trustedReceivedAt;
      return receipt;
    },
    snapshot(series, decisionAt, {maxAge = Infinity} = {}) {
      if (typeof series !== 'string' || !series || !Number.isSafeInteger(decisionAt) ||
          (maxAge !== Infinity && (!Number.isSafeInteger(maxAge) || maxAge < 0))) throw Error('Invalid query');
      const eligible = events.filter(e => e.series === series && e.receivedAt <= decisionAt &&
        e.effectiveAt <= decisionAt && decisionAt - e.effectiveAt <= maxAge);
      if (!eligible.length) return {status:'abstain',reason:'not_available_as_of_decision'};
      eligible.sort((a,b)=>b.receivedAt-a.receivedAt || b.revision-a.revision || a.id.localeCompare(b.id));
      const winner = eligible[0];
      return {status:'available',id:winner.id,value:winner.value,receivedAt:winner.receivedAt,
        effectiveAt:winner.effectiveAt};
    },
    receipts() { return events.map(e=>({...e})); }
  };
}
export function naiveLatest(receipts, series) {
  const items=receipts.filter(e=>e.series===series);
  if (!items.length) return null;
  return items.reduce((a,b)=> b.revision>a.revision || (b.revision===a.revision && b.receivedAt>a.receivedAt)?b:a);
}
export function naivePublishedCutoff(receipts, series, decisionAt) {
  const items=receipts.filter(e=>e.series===series && e.providerPublishedAt<=decisionAt && e.effectiveAt<=decisionAt);
  if (!items.length) return null;
  return items.reduce((a,b)=>b.revision>a.revision || (b.revision===a.revision && b.receivedAt>a.receivedAt)?b:a);
}

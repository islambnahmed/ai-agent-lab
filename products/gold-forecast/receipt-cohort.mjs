/**
 * Fail-closed consistency check for a three-horizon prospective receipt cohort.
 *
 * A crash during issuance may leave only one or two receipt files. Never fill
 * those gaps from a later fetch/code revision: that silently mixes vintages.
 * Existing complete cohorts are immutable; callers must verify each receipt's
 * own content hash before invoking this cross-receipt consistency check.
 */
const HORIZONS = Object.freeze([1, 7, 30]);
const SAME = Object.freeze([
  'schemaVersion', 'issuedAt', 'source', 'codeCommit', 'modelVersion',
  'calendar', 'originDate', 'originClose', 'historyHash', 'historyLength'
]);
const MANIFEST = Object.freeze([
  'url', 'requestedAt', 'receivedAt', 'rawSha256', 'storedSha256'
]);

export function checkReceiptCohort(receipts, expectedOriginDate, verify = () => {}) {
  if (!Array.isArray(receipts) || receipts.length !== HORIZONS.length ||
      typeof expectedOriginDate !== 'string' ||
      !/^\d{4}-\d{2}-\d{2}$/.test(expectedOriginDate) ||
      typeof verify !== 'function') {
    throw new TypeError('Expected three ordered receipt slots and an origin date');
  }
  if (receipts.some(receipt => receipt === undefined)) {
    throw new TypeError('Malformed receipt slot: undefined');
  }
  const present = receipts.filter(receipt => receipt !== null).length;
  if (present === 0) return 'empty';
  if (present !== HORIZONS.length) {
    throw new Error('Partial receipt cohort: do not mix different issuance vintages; inspect and recover manually');
  }
  const first = receipts[0];
  for (let i = 0; i < HORIZONS.length; i++) {
    const receipt = receipts[i];
    if (!receipt || typeof receipt !== 'object' || Array.isArray(receipt)) {
      throw new TypeError('Malformed receipt in cohort');
    }
    verify(receipt);
    if (receipt.horizon !== HORIZONS[i] || receipt.originDate !== expectedOriginDate) {
      throw new Error('Receipt horizon or origin does not match cohort filename');
    }
    if (!receipt.sourceManifest || typeof receipt.sourceManifest !== 'object' ||
        Array.isArray(receipt.sourceManifest)) {
      throw new Error('Missing receipt source manifest');
    }
    if (i === 0) continue;
    for (const field of SAME) {
      if (!Object.is(receipt[field], first[field])) {
        throw new Error('Mixed receipt cohort metadata: ' + field);
      }
    }
    for (const field of MANIFEST) {
      if (!Object.is(receipt.sourceManifest[field], first.sourceManifest[field])) {
        throw new Error('Mixed receipt source snapshots: ' + field);
      }
    }
  }
  return 'complete';
}

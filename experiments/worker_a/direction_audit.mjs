/**
 * Directional forecast audit: separate sign accuracy from willingness to make
 * a directional prediction. A zero forecast move is an abstention, not a loss
 * or a win, even when the realized price is unchanged.
 *
 * Exploratory diagnostic only; no statistical independence or market edge claim.
 */
export function directionAudit(rows, { minMovePct = 0 } = {}) {
  if (!Array.isArray(rows)) throw new TypeError('rows must be an array');
  if (!Number.isFinite(minMovePct) || minMovePct < 0) throw new RangeError('minMovePct must be nonnegative');
  let signals = 0, hits = 0, misses = 0, abstentions = 0, flatActuals = 0;
  for (const row of rows) {
    const { point, actual, originClose } = row ?? {};
    if (![point, actual, originClose].every(Number.isFinite) ||
        point <= 0 || actual <= 0 || originClose <= 0) {
      throw new TypeError('point, actual and originClose must be finite positive prices');
    }
    const predictedMovePct = 100 * (point / originClose - 1);
    const actualSign = Math.sign(actual - originClose);
    if (actualSign === 0) flatActuals++;
    if (Math.abs(predictedMovePct) <= minMovePct) {
      abstentions++;
      continue;
    }
    signals++;
    if (Math.sign(predictedMovePct) === actualSign) hits++;
    else misses++;
  }
  const n = rows.length;
  return {
    n, signals, abstentions, hits, misses, flatActuals,
    participationPct: n ? 100 * signals / n : null,
    accuracyOnSignalsPct: signals ? 100 * hits / signals : null,
    minMovePct,
    interpretation: 'Accuracy is conditional on a non-abstaining directional signal. Serially dependent horizons require separate uncertainty analysis.'
  };
}

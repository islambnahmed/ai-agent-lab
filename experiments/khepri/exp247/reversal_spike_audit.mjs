/**
 * Khepri experiment 247 — advisory reversible-pulse audit for dated positive observations.
 * Does NOT repair/delete points or prove vendor errors. Uses only a matured three-point
 * window, so the most recent observation is never classified without a successor.
 */
function median(values) {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}
export function auditReversalSpikes(rows, {
  minAbsLogMove = 0.08,
  maxResidualFraction = 0.25,
  madMultiplier = 6,
} = {}) {
  if (!Array.isArray(rows) || rows.length < 3) throw new Error('At least three observations required');
  if (![minAbsLogMove, maxResidualFraction, madMultiplier].every(Number.isFinite) ||
      minAbsLogMove <= 0 || maxResidualFraction < 0 || maxResidualFraction > 1 || madMultiplier < 0)
    throw new Error('Invalid audit thresholds');
  let previousDate = '';
  const values = rows.map((row, i) => {
    const date = row?.date;
    const price = row?.price;
    if (typeof date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(date) ||
        !Number.isFinite(Date.parse(date + 'T00:00:00Z')) ||
        new Date(date + 'T00:00:00Z').toISOString().slice(0, 10) !== date ||
        date <= previousDate || typeof price !== 'number' || !Number.isFinite(price) || price <= 0)
      throw new Error('Invalid or unsorted observation at index ' + i);
    previousDate = date;
    return price;
  });
  const returns = values.slice(1).map((p, i) => Math.log(p / values[i]));
  // Median absolute return is robust to symmetric bimodal oscillation;
  // centered MAD can collapse to ~0 when one return sign is one observation more common.
  const robustScale = 1.4826 * median(returns.map(r => Math.abs(r)));
  const threshold = Math.max(minAbsLogMove, madMultiplier * robustScale);
  const flags = [];
  for (let i = 1; i < rows.length - 1; i++) {
    const inbound = returns[i - 1], outbound = returns[i];
    const minMove = Math.min(Math.abs(inbound), Math.abs(outbound));
    const residual = Math.abs(inbound + outbound);
    if (inbound * outbound < 0 && minMove >= threshold &&
        residual <= maxResidualFraction * minMove) {
      flags.push({index: i, date: rows[i].date, inboundLogReturn: inbound,
        outboundLogReturn: outbound, residualLogReturn: inbound + outbound});
    }
  }
  return {
    status: flags.length ? 'review_reversal_pulses' : 'no_detected_reversal_pulses',
    observations: rows.length, thresholdLogReturn: threshold, robustScale,
    flags, caveat: 'Heuristic advisory flag only. Genuine rapid reversals can look identical; never silently edit prices.'
  };
}

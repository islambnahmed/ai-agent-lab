/** Descriptive movement metrics. This is not a trading-performance estimate. */
export function directionMetrics(rows) {
  if (!Array.isArray(rows) || rows.length === 0) throw new Error('Need evaluation rows');
  let directionalCalls = 0, correctCalls = 0, flatActuals = 0, flatPredictions = 0, ternaryMatches = 0;
  for (const r of rows) {
    const values = [r.originClose, r.point, r.actual];
    if (!values.every(v => typeof v === 'number' && Number.isFinite(v) && v > 0)) {
      throw new Error('Invalid forecast or price');
    }
    const predicted = Math.sign(r.point - r.originClose);
    const observed = Math.sign(r.actual - r.originClose);
    if (predicted === 0) flatPredictions++;
    if (observed === 0) flatActuals++;
    if (predicted === observed) ternaryMatches++;
    if (predicted !== 0) {
      directionalCalls++;
      if (predicted === observed) correctCalls++;
    }
  }
  const n = rows.length;
  return {
    n,
    directionalCalls,
    directionalCallRatePct: 100 * directionalCalls / n,
    directionalHitRatePct: directionalCalls ? 100 * correctCalls / directionalCalls : null,
    flatActualRatePct: 100 * flatActuals / n,
    flatPredictionRatePct: 100 * flatPredictions / n,
    ternaryExactMatchPct: 100 * ternaryMatches / n,
    caveat: 'Directional hit rate is conditional on a non-flat forecast; flat realized outcomes count as misses. Null means no directional calls.'
  };
}

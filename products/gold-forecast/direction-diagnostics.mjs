/**
 * Directional evaluation with explicit abstention and minimum-move gates.
 * The gate is on the predicted relative move, never on the realized outcome.
 * No trading-cost or profitability claims are implied by any threshold.
 */
export function directionDiagnostics(rows, {minCallMovePct=0}={}) {
  if (!Array.isArray(rows) || rows.length===0) throw new Error('Nonempty evaluation rows required');
  if (!Number.isFinite(minCallMovePct) || minCallMovePct<0 || minCallMovePct>=100)
    throw new RangeError('minCallMovePct must be in [0,100)');
  let calls=0, hits=0, flatOutcomes=0;
  for (const row of rows) {
    const {point,actual,originClose}=row ?? {};
    if (![point,actual,originClose].every(Number.isFinite) || originClose<=0 || point<=0 || actual<=0)
      throw new Error('Finite positive point, actual and originClose required');
    const realizedSign=Math.sign(actual-originClose);
    if (realizedSign===0) flatOutcomes++;
    const predictedSign=Math.sign(point-originClose);
    if (predictedSign!==0 && 100*Math.abs(point/originClose-1)>minCallMovePct) {
      calls++;
      if (predictedSign===realizedSign) hits++;
    }
  }
  const n=rows.length;
  return {
    n, minCallMovePct, calls, hits, abstentions:n-calls, flatOutcomes,
    callRatePct:100*calls/n,
    hitRateWhenCalledPct:calls ? 100*hits/calls : null,
    abstentionRatePct:100*(n-calls)/n,
    realizedFlatRatePct:100*flatOutcomes/n,
    caveat:'Conditional accuracy is undefined with zero calls; threshold is a signal-size filter, not a transaction-cost model.'
  };
}

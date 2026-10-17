/** Seshat cycle 229: directional skill must not credit unchanged-price ties.
 * Pure diagnostic; no change to model selection, stored forecasts or receipts.
 * Exact comparisons intentionally match forecast.mjs metrics().
 */
export function directionAudit(rows) {
  if (!Array.isArray(rows) || rows.length === 0) throw new TypeError('Nonempty forecast rows required');
  const counts = {n: rows.length, actualFlat: 0, predictedFlat: 0, flatCorrect: 0,
    directionalHits: 0, directionalMisses: 0, directionalAbstentions: 0, falseMoveOnFlat: 0};
  for (const row of rows) {
    if (![row?.originClose, row?.point, row?.actual].every(x=>typeof x==='number' && Number.isFinite(x) && x>0))
      throw new TypeError('Finite positive originClose, point and actual required');
    const predicted = Math.sign(row.point-row.originClose);
    const actual = Math.sign(row.actual-row.originClose);
    if (predicted === 0) counts.predictedFlat++;
    if (actual === 0) counts.actualFlat++;
    if (actual === 0 && predicted === 0) counts.flatCorrect++;
    else if (actual === 0) counts.falseMoveOnFlat++;
    else if (predicted === 0) counts.directionalAbstentions++;
    else if (predicted === actual) counts.directionalHits++;
    else counts.directionalMisses++;
  }
  const active = counts.directionalHits+counts.directionalMisses;
  const nonflat = rows.length-counts.actualFlat;
  const rate = (a,b)=>b===0?null:100*a/b;
  return {...counts, nonflatTargets:nonflat, activeDirectionalPredictionsOnNonflat:active,
    legacyDirectionAccuracy:rate(counts.flatCorrect+counts.directionalHits,rows.length),
    activeDirectionAccuracy:rate(counts.directionalHits,active),
    directionalCoverageOnNonflat:rate(active,nonflat),
    directionalHitRateOnNonflat:rate(counts.directionalHits,nonflat),
    flatTargetRate:rate(counts.actualFlat,rows.length),
    note:'A correct no-change prediction is not evidence of up/down directional skill. Null rates mean no eligible observations.'};
}

/** For persistence point === originClose. The legacy directionAccuracy is
 * exactly the percentage of targets unchanged from the origin.
 */
export function persistenceTieCount(metric, {tolerance=1e-7}={}) {
  const n=metric?.n, pct=metric?.directionAccuracy;
  if (!Number.isInteger(n) || n<=0 || typeof pct!=='number' || !Number.isFinite(pct) || pct<0 || pct>100)
    throw new TypeError('Expected n>0 and directionAccuracy in [0,100]');
  const unrounded=n*pct/100, ties=Math.round(unrounded);
  if (Math.abs(unrounded-ties)>tolerance) throw new RangeError('Published percentage cannot reconstruct an integer count');
  return {n,unchangedTargets:ties,changedTargets:n-ties,unchangedRatePct:100*ties/n,
    directionalPredictions:0,interpretation:'All legacy correct-direction credits arise from unchanged targets, not directional predictions'};
}

export function auditReadinessReport(report) {
  if (!Array.isArray(report?.horizons)) throw new TypeError('Expected readiness horizons');
  return report.horizons.map(h=>{
    if (!Number.isInteger(h.horizon)) throw new TypeError('Invalid horizon');
    const baseline=persistenceTieCount(h.baseline);
    const selection=h.candidates?.find(c=>c.model==='persistence');
    const validation=selection?persistenceTieCount(selection.validation):null;
    return {horizon:h.horizon,model:h.model,source:report.source,calendar:h.calendar,
      audit:baseline,validation,
      limits:'Aggregate-derived counts only. Cannot determine dates, market cause or model directional skill without individual rows.'};
  });
}

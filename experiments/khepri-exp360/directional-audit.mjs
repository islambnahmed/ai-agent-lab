/** Experimental audit for point forecasts. Not a trading or model-promotion signal.
 * Input rows: {point, actual, originClose}; all prices/levels positive and finite.
 * Threshold is a minimum absolute forecast move relative to originClose.
 */
export function directionalAudit(rows, thresholds=[0, 0.001, 0.005]) {
  if (!Array.isArray(rows) || rows.length === 0) throw Error('Nonempty rows required');
  if (!Array.isArray(thresholds) || thresholds.length === 0 ||
      thresholds.some(x => !Number.isFinite(x) || x < 0 || x >= 1)) throw Error('Invalid thresholds');
  for (const r of rows) {
    if (!r || [r.point,r.actual,r.originClose].some(x=>typeof x !== 'number' || !Number.isFinite(x) || x<=0))
      throw Error('Invalid evaluation row');
  }
  return thresholds.map(threshold => {
    let calls=0, correct=0, incorrect=0, abstentions=0, flatActual=0;
    for (const r of rows) {
      const predictedMove=(r.point-r.originClose)/r.originClose;
      const actualMove=r.actual-r.originClose;
      if (actualMove===0) flatActual++;
      if (Math.abs(predictedMove)<=threshold) {abstentions++;continue;}
      calls++;
      if (Math.sign(predictedMove)===Math.sign(actualMove)) correct++;
      else incorrect++;
    }
    return {threshold, total:rows.length, calls, abstentions, correct, incorrect,
      flatActual, callRate:calls/rows.length,
      conditionalHitRate:calls ? correct/calls : null,
      unconditionalCorrectShare:correct/rows.length};
  });
}

/** Exact directional expression from main/products/gold-forecast/forecast.mjs,
 * retrieved 2026-10-22, for comparative regression reproduction.
 */
export function legacyDirectionAccuracy(rows) {
  const mean=xs=>xs.reduce((a,b)=>a+b,0)/xs.length;
  return 100*mean(rows.map(r=>Math.sign(r.point-r.originClose)===Math.sign(r.actual-r.originClose)?1:0));
}

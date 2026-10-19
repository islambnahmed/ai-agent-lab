/** Khepri experiment 301: directional-score identifiability diagnostic.
 * Pure function; no market or external I/O. Does not modify the gold model.
 */
const sign = x => Math.sign(x);
function assertRow(r) {
  if (!r || !['point','actual','originClose'].every(k=>typeof r[k]==='number' && Number.isFinite(r[k]) && r[k]>0))
    throw Error('point, actual, originClose must be finite positive numbers');
}
export function auditDirection(rows) {
  if (!Array.isArray(rows) || !rows.length) throw Error('nonempty rows required');
  rows.forEach(assertRow);
  let legacyHits=0, neutralForecasts=0, activeHits=0, upActual=0, downActual=0, flatActual=0;
  let upOnActive=0, downOnActive=0, flatOnActive=0;
  for (const r of rows) {
    const f=sign(r.point-r.originClose), a=sign(r.actual-r.originClose);
    legacyHits += Number(f===a);
    if (a===1) upActual++; else if (a===-1) downActual++; else flatActual++;
    if (f===0) {neutralForecasts++; continue;}
    activeHits+=Number(f===a);
    if(a===1)upOnActive++; else if(a===-1)downOnActive++; else flatOnActive++;
  }
  const n=rows.length, active=n-neutralForecasts;
  const majorityActive=Math.max(upOnActive,downOnActive,flatOnActive);
  return {
    n, legacyAccuracyPct:100*legacyHits/n,
    neutralForecasts, neutralRatePct:100*neutralForecasts/n,
    active, conditionalAccuracyPct:active?100*activeHits/active:null,
    majorityActualRateOnActivePct:active?100*majorityActive/active:null,
    excessVsMajorityOnActivePct:active?100*(activeHits-majorityActive)/active:null,
    actualCounts:{up:upActual,down:downActual,flat:flatActual},
    warning:'Neutral point forecasts are a distinct class, not evidence of directional incompetence; conditional scores are selection-dependent and not predictive skill.'
  };
}
export function meanAbsoluteError(rows) {
  if (!Array.isArray(rows) || !rows.length) throw Error('nonempty rows required');
  rows.forEach(assertRow);
  return rows.reduce((s,r)=>s+Math.abs(r.point-r.actual),0)/rows.length;
}
export function flatBaseline(rows) {
  return rows.map(r=>({ ...r,point:r.originClose }));
}
export function tinyUpBaseline(rows,eps=1e-9) {
  if (!Number.isFinite(eps) || eps<=0) throw Error('positive epsilon required');
  return rows.map(r=>({ ...r,point:r.originClose+eps }));
}

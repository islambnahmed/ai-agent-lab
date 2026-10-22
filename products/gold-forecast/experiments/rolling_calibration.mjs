/**
 * Exploratory, causally updated interval calibration. NOT production code.
 * Rows are forecast-origin observations with a nonnegative normalized absolute
 * error; their error only becomes knowable at originIndex + horizon.
 * The evaluation may be retrospective; it cannot establish prospective coverage.
 */
function assertRows(rows, label) {
  if (!Array.isArray(rows) || !rows.length) throw Error(`${label} must be nonempty`);
  let last = -1;
  for (const row of rows) {
    if (!Number.isSafeInteger(row.originIndex) || row.originIndex <= last ||
        !Number.isFinite(row.bandError) || row.bandError < 0)
      throw Error(`Invalid or unsorted ${label} row`);
    last = row.originIndex;
  }
}

export function finiteOrderBand(errors, {target=0.8, floor=0.002}={}) {
  if (!Array.isArray(errors) || !errors.length ||
      errors.some(x => !Number.isFinite(x) || x < 0) ||
      !Number.isFinite(target) || target <= 0 || target >= 1 ||
      !Number.isFinite(floor) || floor < 0) throw Error('Invalid band inputs');
  const sorted = [...errors].sort((a,b)=>a-b);
  const rank = Math.min(sorted.length, Math.ceil((sorted.length+1)*target));
  return Math.max(floor, sorted[rank-1]);
}

export function evaluateCausalRolling({calibrationRows, auditRows, horizon,
    window=120, minSamples=40, target=0.8, floor=0.002}={}) {
  assertRows(calibrationRows, 'calibration');
  assertRows(auditRows, 'audit');
  if (!Number.isSafeInteger(horizon) || horizon < 1 ||
      !Number.isSafeInteger(window) || window < 1 ||
      !Number.isSafeInteger(minSamples) || minSamples < 1 || minSamples > window ||
      calibrationRows.at(-1).originIndex >= auditRows[0].originIndex)
    throw Error('Invalid chronology or fixed settings');
  // Purged calibration labels must have matured before the first audit origin.
  if (calibrationRows.at(-1).originIndex + horizon > auditRows[0].originIndex)
    throw Error('Calibration label not yet mature at first audit origin');
  const staticBand = finiteOrderBand(calibrationRows.map(r=>r.bandError), {target,floor});
  const known = [...calibrationRows];
  let nextAuditToMature = 0;
  const result=[];
  for (const row of auditRows) {
    // A prediction issued at index j only gets its label at index j+h.
    // Never use the current row's error or another immature audit label.
    while (nextAuditToMature < auditRows.length &&
        auditRows[nextAuditToMature].originIndex + horizon <= row.originIndex) {
      known.push(auditRows[nextAuditToMature++]);
    }
    const recent = known.filter(r => r.originIndex + horizon <= row.originIndex)
      .sort((a,b)=>a.originIndex-b.originIndex).slice(-window);
    if (recent.length < minSamples) throw Error('Insufficient matured calibration errors');
    const band=finiteOrderBand(recent.map(r=>r.bandError), {target,floor});
    result.push({originIndex:row.originIndex, band, staticBand,
      rollingHit:row.bandError <= band, staticHit:row.bandError <= staticBand,
      maturedCount:recent.length});
  }
  const avg = (key) => result.reduce((sum,r)=>sum+r[key],0)/result.length;
  return {horizon, window, minSamples, target, floor, staticBand,
    n:result.length, rollingCoveragePct:100*avg('rollingHit'),
    staticCoveragePct:100*avg('staticHit'),
    meanRollingHalfWidthPct:100*avg('band'),
    meanStaticHalfWidthPct:100*staticBand,
    rows:result,
    limitations:['No exchangeability or independence guarantee',
      'Overlapping horizon errors are dependent',
      'Historical audit has been inspected; not a fresh blind test',
      'Hyperparameters must be fixed before prospective evaluation']};
}

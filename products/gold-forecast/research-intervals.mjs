// Research-only, prequential interval audit. Never auto-promote to the live forecast.
// A residual from origin i with horizon h is usable only at origins >= i+h.
const positive = (x) => Number.isFinite(x) && x > 0;
function checkRows(rows, label) {
  if (!Array.isArray(rows) || !rows.length) throw Error('Missing ' + label + ' rows');
  let last = -1;
  for (const row of rows) {
    if (!Number.isInteger(row.originIndex) || row.originIndex <= last ||
        !positive(row.point) || !positive(row.actual)) throw Error('Invalid or unordered ' + label + ' row');
    last = row.originIndex;
  }
}
export function finiteBand(errors, coverage = 0.8, floor = 0.002) {
  if (!Array.isArray(errors) || !errors.length || errors.some(e => !Number.isFinite(e) || e < 0) ||
      !Number.isFinite(coverage) || coverage <= 0 || coverage >= 1 || !positive(floor)) {
    throw Error('Invalid band inputs');
  }
  const sorted = [...errors].sort((a,b) => a-b);
  const rank = Math.min(sorted.length, Math.ceil((sorted.length + 1) * coverage));
  return Math.max(floor, sorted[rank - 1]);
}
const error = row => Math.abs(row.actual - row.point) / row.point;
const summary = rows => ({
  n: rows.length,
  coveragePct: 100 * rows.filter(r => r.hit).length / rows.length,
  meanHalfWidthPct: 100 * rows.reduce((s,r) => s + r.band, 0) / rows.length
});
export function auditRollingIntervals({calibrationRows, auditRows, horizon, window = 120,
                                      minMatured = 30, coverage = 0.8} = {}) {
  if (!Number.isInteger(horizon) || horizon < 1 || horizon > 30 ||
      !Number.isInteger(window) || window < 1 ||
      !Number.isInteger(minMatured) || minMatured < 1 || minMatured > window) {
    throw Error('Invalid causal audit settings');
  }
  checkRows(calibrationRows, 'calibration');
  checkRows(auditRows, 'audit');
  if (calibrationRows.at(-1).originIndex >= auditRows[0].originIndex) {
    throw Error('Calibration and audit origins overlap');
  }
  const firstOrigin = auditRows[0].originIndex;
  const maturedBeforeAudit = calibrationRows.filter(r => r.originIndex + horizon <= firstOrigin);
  if (maturedBeforeAudit.length < minMatured) throw Error('Insufficient matured calibration labels');
  // Frozen benchmark uses ALL eligible calibration residuals, exactly as the static method.
  const frozenBand = finiteBand(maturedBeforeAudit.map(error), coverage);
  const records = auditRows.map((row, i) => {
    // The origin cutoff is inclusive for a label that has just matured at the origin.
    const eligible = [...calibrationRows, ...auditRows.slice(0,i)]
      .filter(r => r.originIndex + horizon <= row.originIndex)
      .slice(-window);
    const band = eligible.length >= minMatured ? finiteBand(eligible.map(error),coverage) : frozenBand;
    const e = error(row);
    return {originIndex:row.originIndex, band, frozenBand,
      hit:e <= band, frozenHit:e <= frozenBand, maturedCount:eligible.length};
  });
  const adaptive = summary(records);
  const frozen = summary(records.map(r => ({band:r.frozenBand,hit:r.frozenHit})));
  const tail = records.slice(Math.floor(records.length/2));
  return {schemaVersion:1, researchOnly:true, horizon, window, minMatured, coverageTargetPct:coverage*100,
    frozenBand, adaptive, frozen, tailAdaptive:summary(tail),
    tailFrozen:summary(tail.map(r=>({band:r.frozenBand,hit:r.frozenHit}))), records,
    caveats:['Retrospective prequential simulation; only labels matured by each origin are eligible',
      'No independence or nominal-coverage guarantee under distribution shift',
      'Audit inspection does not authorize production promotion or tuning on this holdout']};
}

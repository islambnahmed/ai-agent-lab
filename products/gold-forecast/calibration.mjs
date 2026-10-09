// Forecast-centered multiplicative intervals. Calibration outcomes must precede audit.
// Descriptive coverage only: no guarantee under dependence or regime shift.
function quantileNearestRank(values, probability) {
  if (!values.length || values.some(x => !Number.isFinite(x) || x < 0))
    throw new Error('Need finite nonnegative calibration errors');
  if (!(probability > 0 && probability < 1)) throw new Error('Invalid quantile');
  const sorted = [...values].sort((a,b) => a-b);
  return sorted[Math.ceil(sorted.length * probability) - 1];
}
export function logError(predicted, actual) {
  if (![predicted,actual].every(x => Number.isFinite(x) && x > 0))
    throw new Error('Prices must be finite positive values');
  return Math.abs(Math.log(actual / predicted));
}
export function calibrateMultiplicativeInterval(calibrationPairs, probability=0.8, floor=0.002) {
  if (!Array.isArray(calibrationPairs) || calibrationPairs.length === 0)
    throw new Error('No calibration pairs');
  const errors = calibrationPairs.map(({predicted,actual})=>logError(predicted,actual));
  const logRadius = Math.max(Math.log1p(floor),quantileNearestRank(errors,probability));
  return {logRadius,band:Math.expm1(logRadius),n:errors.length};
}
export function intervalAt(predicted, logRadius) {
  if (!Number.isFinite(predicted) || predicted <= 0 || !Number.isFinite(logRadius) || logRadius < 0)
    throw new Error('Invalid interval input');
  return {lower:predicted*Math.exp(-logRadius),upper:predicted*Math.exp(logRadius)};
}
export function empiricalCoverage(auditPairs, logRadius) {
  if (!Array.isArray(auditPairs) || !auditPairs.length) throw new Error('No audit pairs');
  const tolerance = 1e-12;
  return 100*auditPairs.filter(({predicted,actual})=>logError(predicted,actual) <= logRadius+tolerance).length/auditPairs.length;
}

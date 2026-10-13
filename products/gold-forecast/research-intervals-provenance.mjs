// Research-only, opt-in exact row identity check. The expected digest must come
// from a separately committed/dated frozen receipt; self-comparison proves nothing.
import {createHash} from 'node:crypto';
import {auditHistoricalIntervals} from './research-intervals-history.mjs';

const fields = ['originIndex','originDate','targetDate','originClose','point','actual','bandError'];
const rowsPayload = rows => rows.map(row => fields.map(key => {
  if (!Object.hasOwn(row, key)) throw Error('Missing row field: ' + key);
  const value = row[key];
  if (typeof value === 'number' && !Number.isFinite(value)) throw Error('Nonfinite row field: ' + key);
  return value;
}));
export function frozenRowsSha256(forecast) {
  if (!forecast?.rows || !Array.isArray(forecast.rows.calibration) ||
      !Array.isArray(forecast.rows.audit) || ![1,7,30].includes(forecast.horizon) ||
      typeof forecast.model !== 'string' || typeof forecast.calendar !== 'string') {
    throw Error('Invalid frozen forecast rows');
  }
  const payload = [1, forecast.horizon, forecast.model, forecast.calendar,
    rowsPayload(forecast.rows.calibration), rowsPayload(forecast.rows.audit)];
  return createHash('sha256').update(JSON.stringify(payload)).digest('hex');
}
export function auditHistoricalIntervalsVerified(forecast, expectedRowsSha256, options = {}) {
  if (typeof expectedRowsSha256 !== 'string' || !/^[0-9a-f]{64}$/.test(expectedRowsSha256)) {
    throw Error('Expected independently anchored SHA-256 digest');
  }
  const actual = frozenRowsSha256(forecast);
  if (actual !== expectedRowsSha256) throw Error('Frozen row identity mismatch');
  const result = auditHistoricalIntervals(forecast, options);
  return {...result, frozenRowsSha256:actual, rowIdentityVerified:true,
    provenanceCaveat:'Digest equality only proves identity to the separately anchored expected digest; it does not authenticate provider prices.'};
}

// Research-only adapter: evaluate the exact frozen forecast's historical rows.
// Never feed this result to the live forecast or retune on the inspected audit.
import {auditRollingIntervals} from './research-intervals.mjs';

const compact = rows => rows.map(({originIndex, point, actual}) => ({originIndex, point, actual}));

export function auditHistoricalIntervals(frozenForecast, {window = 120, minMatured = 30, coverage = 0.8} = {}) {
  if (!frozenForecast || ![1, 7, 30].includes(frozenForecast.horizon) ||
      !frozenForecast.rows || !Array.isArray(frozenForecast.rows.calibration) ||
      !Array.isArray(frozenForecast.rows.audit) ||
      !Number.isFinite(frozenForecast.band) || !Number.isFinite(frozenForecast.coverage)) {
    throw Error('Expected a forecast with includeRows:true');
  }
  const result = auditRollingIntervals({
    calibrationRows: compact(frozenForecast.rows.calibration),
    auditRows: compact(frozenForecast.rows.audit),
    horizon: frozenForecast.horizon, window, minMatured, coverage
  });
  // This must be an apples-to-apples comparison with the frozen model's actual
  // calibration and audit rows, not a fresh split or a different point forecast.
  if (Math.abs(result.frozenBand - frozenForecast.band) > 1e-10 ||
      Math.abs(result.frozen.coveragePct - frozenForecast.coverage) > 1e-8) {
    throw Error('Frozen forecast parity failed: different split, rows or quantile');
  }
  return {
    schemaVersion: 1, researchOnly: true, model: frozenForecast.model,
    horizon: frozenForecast.horizon, horizonUnit: frozenForecast.horizonUnit,
    calendar: frozenForecast.calendar, auditedFrom: frozenForecast.auditedFrom,
    calibrationN: frozenForecast.rows.calibration.length,
    ...result,
    caution: 'Retrospective prequential interval audit on already-inspected data. No live deployment or market-edge claim.'
  };
}

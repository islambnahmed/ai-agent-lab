/** Fail-closed historical-data adapter used by the Gold Lab UI.
 * Never replaces rejected market observations with synthetic values.
 * Source-vintage authenticity and price-provider reliability remain unverified.
 */
import {validateHistoricalCloses} from './historical-integrity.mjs';

export function prepareProviderHistory(payload, asOf) {
  if (!payload || payload.metal !== 'XAU' || !Array.isArray(payload.points)) {
    throw Error('Unexpected historical data format');
  }
  return validateHistoricalCloses(payload.points, {
    asOf, minRows: 165, requireFresh: true, maxAgeDays: 7
  });
}

/** A deliberately simple two-column CSV format; reject ambiguous quoting,
 * missing cells, malformed rows and duplicates instead of silently dropping them.
 */
export function prepareCsvHistory(text, asOf) {
  if (typeof text !== 'string') throw Error('CSV must be text');
  const lines = text.replace(/^\uFEFF/, '').trim().split(/\r?\n/);
  const columns = lines.shift()?.split(',').map(s => s.trim().toLowerCase()) ?? [];
  if (columns.length < 2 || new Set(columns).size !== columns.length) throw Error('Invalid CSV header');
  const di = columns.findIndex(s => ['date','t','timestamp'].includes(s));
  const pi = columns.findIndex(s => ['price','close'].includes(s));
  if (di < 0 || pi < 0 || di === pi) throw Error('CSV needs date,price or Date,Close columns');
  const rows = lines.map((line, i) => {
    const cells = line.split(',');
    if (cells.length !== columns.length || cells.some(s => s.trim() === '')) {
      throw Error('Invalid CSV row '+(i+2));
    }
    return {date:cells[di].trim(),price:cells[pi].trim()};
  });
  return validateHistoricalCloses(rows, {
    asOf, minRows: 165, requireFresh: false
  });
}

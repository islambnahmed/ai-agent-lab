// Reconcile an immutable receipt with a refreshed, rolling provider history.
// A missing local vintage is recoverable ONLY when the refreshed feed contains
// the entire original history at the canonical row level.
// Never infer, forward-fill or silently accept revised historical closes.
import {createHash} from 'node:crypto';

const hash = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');

export function reconcileVintage(receipt, refreshed, frozen = null) {
  if (!receipt || !Number.isInteger(receipt.historyLength) || receipt.historyLength < 1 ||
      !/^[0-9a-f]{64}$/.test(receipt.historyHash ?? '') ||
      typeof receipt.originDate !== 'string') throw Error('Invalid receipt vintage metadata');
  if (!Array.isArray(refreshed) || !refreshed.length) throw Error('Refreshed history missing');

  const authentic = rows => Array.isArray(rows) &&
    rows.length === receipt.historyLength &&
    rows.at(-1)?.date === receipt.originDate &&
    hash(rows) === receipt.historyHash;

  if (frozen === null) {
    const prefix = refreshed.slice(0, receipt.historyLength);
    if (!authentic(prefix))
      throw Error('Original vintage unavailable; refreshed history does not reproduce receipt hash');
    return refreshed;
  }

  if (!authentic(frozen)) throw Error('Original local vintage corrupted or mismatched');
  const prices = new Map(frozen.map(row => [row.date, row.price]));
  if (!refreshed.some(row => row.date === receipt.originDate))
    throw Error('Origin missing from refreshed source; continuity unverified');
  for (const row of refreshed) {
    if (prices.has(row.date) && prices.get(row.date) !== row.price)
      throw Error('Provider revised historical vintage: ' + row.date);
  }
  return frozen.concat(refreshed.filter(row => row.date > receipt.originDate));
}

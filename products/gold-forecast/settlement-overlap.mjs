/**
 * Validate that a refreshed rolling vendor feed preserves the frozen
 * forecast-origin overlap. The caller must validate unique sorted dates and
 * finite prices before invoking this helper.
 */
export function reconcileSettlementHistory(frozen, refreshed, originDate) {
  if (!Array.isArray(frozen) || !frozen.length ||
      !Array.isArray(refreshed) || !refreshed.length ||
      frozen.at(-1)?.date !== originDate) {
    throw Error('Invalid frozen origin or refreshed history');
  }
  const original = new Map(frozen.map(row => [row.date, row.price]));
  const seen = new Set();
  for (const row of refreshed) {
    if (row.date > originDate) continue;
    if (!original.has(row.date))
      throw Error('Provider inserted historical observation: ' + row.date);
    if (original.get(row.date) !== row.price)
      throw Error('Provider revised historical vintage: ' + row.date);
    seen.add(row.date);
  }
  if (!seen.has(originDate))
    throw Error('Origin missing from refreshed source');
  const overlapStart = refreshed[0].date;
  for (const row of frozen) {
    if (row.date >= overlapStart && !seen.has(row.date))
      throw Error('Provider removed historical observation inside overlap: ' + row.date);
  }
  return frozen.concat(refreshed.filter(row => row.date > originDate));
}

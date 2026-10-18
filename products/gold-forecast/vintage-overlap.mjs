/**
 * Reject changes to the historical calendar and prices within the portion of
 * an immutable forecast vintage still visible in a rolling provider feed.
 * Both inputs must be strictly sorted, unique, validated close arrays.
 */
export function assertVintageOverlap(frozen, refreshed, originDate) {
  if (!Array.isArray(frozen) || !frozen.length ||
      !Array.isArray(refreshed) || !refreshed.length ||
      frozen.at(-1)?.date !== originDate) {
    throw Error('Invalid frozen vintage or origin');
  }
  const firstVisible = refreshed[0].date;
  const historical = refreshed.filter(r => r.date <= originDate);
  if (!historical.length || historical.at(-1).date !== originDate) {
    throw Error('Origin missing from refreshed source');
  }
  const overlap = frozen.filter(r => r.date >= firstVisible);
  if (overlap.length !== historical.length) {
    throw Error('Provider revised historical vintage dates in visible overlap');
  }
  for (let i = 0; i < overlap.length; i++) {
    if (overlap[i].date !== historical[i].date) {
      throw Error('Provider revised historical vintage dates in visible overlap');
    }
    if (overlap[i].price !== historical[i].price) {
      throw Error('Provider revised historical vintage price: ' + overlap[i].date);
    }
  }
  return { compared: overlap.length, leftTruncated: firstVisible > frozen[0].date };
}

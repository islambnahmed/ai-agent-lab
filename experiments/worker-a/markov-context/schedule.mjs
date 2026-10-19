/** Local causal feedback delivery scheduler, identical to cycle 230 logic. */
export function seeded(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export function schedule(stream, {seed=999, maxLag=0, drop=.0, dropout='mcar'} = {}) {
  if (!Number.isInteger(maxLag) || maxLag < 0 || !(drop >= 0 && drop <= 1) || !['mcar','hard'].includes(dropout)) throw Error('Invalid delivery parameters');
  const rand = seeded(seed), deliveries = new Map();
  let lost = 0, scheduled = 0;
  for (const [eventTime, row] of stream.entries()) {
    const hard = row.x[0] !== row.y;
    const p = dropout === 'hard' ? (hard ? drop : 0) : drop;
    if (rand() < p) {lost++; continue;}
    const lag = Math.floor(rand() * (maxLag + 1));
    const deliveryTime = eventTime + 1 + lag;
    if (!deliveries.has(deliveryTime)) deliveries.set(deliveryTime, []);
    deliveries.get(deliveryTime).push({eventTime, x:row.x, y:row.y});
    scheduled++;
  }
  return {deliveries, lost, scheduled};
}

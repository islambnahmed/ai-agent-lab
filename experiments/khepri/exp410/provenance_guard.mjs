/** Research-only deterministic point-in-time provenance guard.
 * No external IO. It deliberately fails closed on ambiguous top-ranked
 * source/vintage ties instead of silently choosing input order.
 */
import {parseInstant} from './historical-integrity.mjs';
const FIELDS=new Set(['feature','value','observedAt','availableAt','source','vintage']);

export function guardedFeatures(records, originAt, {maxAgeDays=30}={}) {
  const origin = parseInstant(originAt);
  if (!Number.isFinite(maxAgeDays) || maxAgeDays < 0) throw Error('Invalid feature age limit');
  if (!Array.isArray(records)) throw Error('Expected feature records array');
  const byFeature = new Map();
  for (const row of records) {
    if (!row || typeof row.feature !== 'string' || !row.feature ||
        typeof row.source !== 'string' || !row.source ||
        typeof row.vintage !== 'string' || !row.vintage ||
        !Number.isFinite(row.value) ||
        Object.keys(row).some(k=>!FIELDS.has(k))) throw Error('Invalid feature record');
    const observed = parseInstant(row.observedAt);
    const available = parseInstant(row.availableAt);
    if (available < observed) throw Error('Feature available before observation');
    if (observed > origin || available > origin) continue;
    const group = byFeature.get(row.feature) ?? [];
    group.push({row, observed, available});
    byFeature.set(row.feature, group);
  }
  const entries = [];
  for (const [key, group] of byFeature) {
    const observed = group.reduce((m,x)=>Math.max(m,x.observed),-Infinity);
    const sameObs = group.filter(x=>x.observed===observed);
    const available = sameObs.reduce((m,x)=>Math.max(m,x.available),-Infinity);
    const finalists = sameObs.filter(x=>x.available===available);
    const signatures = new Set(finalists.map(x=>JSON.stringify([
      x.row.source, x.row.vintage, x.row.value,
      x.observed, x.available
    ])));
    if (signatures.size > 1) throw Error('Ambiguous top-ranked feature provenance: '+key);
    const row = finalists[0].row;
    entries.push([key, {feature:row.feature, value:row.value,
      observedAt:new Date(observed).toISOString(),
      availableAt:new Date(available).toISOString(),
      source:row.source, vintage:row.vintage,
      ageDays:(origin-observed)/86400000,
      stale:origin-observed>maxAgeDays*86400000}]);
  }
  // Sorted keys and Object.fromEntries protect __proto__ and stable JSON hashes.
  return Object.fromEntries(entries.sort((a,b)=>a[0]<b[0]?-1:a[0]>b[0]?1:0));
}

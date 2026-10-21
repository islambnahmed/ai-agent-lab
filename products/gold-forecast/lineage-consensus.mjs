// Research-only quote corroboration. This is NOT proof of independent upstreams.
// The roster must be independently audited and frozen at the evaluation origin.
const validInstant = (value) => typeof value === 'string' &&
  /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$/.test(value) &&
  Number.isFinite(Date.parse(value));
const nonempty = (s) => typeof s === 'string' && s.trim().length > 0;
const median = (xs) => { const a = [...xs].sort((x, y) => x - y); return a.length % 2 ? a[(a.length-1)/2] : (a[a.length/2-1]+a[a.length/2])/2; };
const close = (a, b, tolerance) => Math.abs(a-b) <= tolerance * Math.min(a,b);

export function assessLineageConsensus(quotes, roster, {
  originAt, maxAgeMs = 300000, tolerance = 0.001,
  minIndependentRoots = 3, minRosterCoverage = 0.6,
} = {}) {
  if (!Array.isArray(quotes) || !Array.isArray(roster) || !validInstant(originAt) ||
      !Number.isFinite(maxAgeMs) || maxAgeMs < 0 ||
      !Number.isFinite(tolerance) || tolerance < 0 || tolerance >= 1 ||
      !Number.isInteger(minIndependentRoots) || minIndependentRoots < 2 ||
      !Number.isFinite(minRosterCoverage) || minRosterCoverage <= 0 || minRosterCoverage > 1) {
    throw new Error('Invalid consensus inputs');
  }
  const origin = Date.parse(originAt);
  const providers = new Map();
  for (const row of roster) {
    if (!nonempty(row?.provider) || providers.has(row.provider)) throw new Error('Invalid or duplicate roster provider');
    providers.set(row.provider, row);
  }
  if (providers.size === 0) throw new Error('Empty expected roster');
  const quoteGroups = new Map();
  for (const quote of quotes) {
    if (!nonempty(quote?.provider) || !providers.has(quote.provider)) continue;
    if (!quoteGroups.has(quote.provider)) quoteGroups.set(quote.provider, []);
    quoteGroups.get(quote.provider).push(quote);
  }
  const eligible = [];
  const excluded = {};
  for (const [provider, info] of providers) {
    const rows = quoteGroups.get(provider) || [];
    let reason = null;
    if (!nonempty(info.root) || !nonempty(info.evidenceRef) || !validInstant(info.auditedAt) ||
        Date.parse(info.auditedAt) > origin || !nonempty(info.convention)) reason = 'lineage_unverified_as_of_origin';
    else if (rows.length !== 1) reason = rows.length ? 'duplicate_provider_quotes' : 'missing_quote';
    else {
      const quote = rows[0];
      if (!Number.isFinite(quote.price) || quote.price <= 0 ||
          quote.convention !== info.convention || !validInstant(quote.observedAt)) reason = 'invalid_quote_or_convention';
      else if (Date.parse(quote.observedAt) > origin) reason = 'future_quote';
      else if (origin - Date.parse(quote.observedAt) > maxAgeMs) reason = 'stale_quote';
      else eligible.push({ provider, root: info.root, price: quote.price, convention: info.convention });
    }
    if (reason) excluded[provider] = reason;
  }
  const byRoot = new Map();
  for (const q of eligible) {
    const key = JSON.stringify([q.root, q.convention]);
    if (!byRoot.has(key)) byRoot.set(key, []);
    byRoot.get(key).push(q);
  }
  const roots = [];
  for (const group of byRoot.values()) {
    const prices = group.map(x => x.price);
    if (!close(Math.min(...prices), Math.max(...prices), tolerance)) {
      for (const q of group) excluded[q.provider] = 'conflicting_same_root';
    } else roots.push({ root: group[0].root, convention: group[0].convention, price: median(prices) });
  }
  // A root can only contribute once, even if several feeds or conventions report it.
  const rootKeys = new Map();
  for (const item of roots) {
    if (!rootKeys.has(item.root)) rootKeys.set(item.root, []);
    rootKeys.get(item.root).push(item);
  }
  const usableRoots = roots.filter(x => rootKeys.get(x.root).length === 1);
  const usableKeys = new Set(usableRoots.map(x => JSON.stringify([x.root,x.convention])));
  const validEligible = eligible.filter(q => usableKeys.has(JSON.stringify([q.root,q.convention])));
  for (const q of eligible) if (!usableKeys.has(JSON.stringify([q.root,q.convention])) && !excluded[q.provider]) {
    excluded[q.provider] = 'root_multiple_conventions';
  }
  const coverage = validEligible.length / providers.size;
  const conventions = new Set(validEligible.map(x => x.convention));
  const base = { eligibleProviders: validEligible.length, expectedProviders: providers.size,
    rosterCoverage: coverage, eligibleRoots: usableRoots.length, excluded };
  if (coverage < minRosterCoverage) return { status: 'insufficient_evidence', reason: 'roster_coverage', ...base };
  if (conventions.size !== 1) return { status: 'insufficient_evidence', reason: 'mixed_conventions', ...base };
  if (usableRoots.length < minIndependentRoots) return { status: 'insufficient_evidence', reason: 'insufficient_roots', ...base };
  const ordered = [...usableRoots].sort((a,b) => a.price-b.price || a.root.localeCompare(b.root));
  const windows = [];
  for (let i=0; i<ordered.length; i++) {
    for (let j=i; j<ordered.length && close(ordered[i].price, ordered[j].price, tolerance); j++) {
      windows.push(ordered.slice(i,j+1));
    }
  }
  const bestSize = Math.max(...windows.map(x=>x.length));
  if (bestSize < minIndependentRoots) return { status:'insufficient_evidence', reason:'no_independent_consensus', ...base };
  const winners = new Map();
  for (const window of windows.filter(x=>x.length===bestSize)) {
    const key = window.map(x=>x.root).sort().join('\u0000');
    winners.set(key, window);
  }
  if (winners.size !== 1) return { status:'insufficient_evidence', reason:'ambiguous_clusters', ...base };
  const group = [...winners.values()][0];
  return { status:'corroborated_quotes', reason:'audited_root_quorum',
    roots: group.map(x=>x.root).sort(), representativePrice:median(group.map(x=>x.price)), ...base };
}

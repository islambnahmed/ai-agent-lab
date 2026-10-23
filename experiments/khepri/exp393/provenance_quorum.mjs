/**
 * Provenance-aware numeric corroboration (synthetic lab prototype).
 * It verifies agreement, NOT ground truth or the truth of provenance claims.
 * No network I/O, secrets, or external effects.
 */
export function corroborate(observations, {tolerance = 0.01, quorum = 2, trustLineage = true} = {}) {
  if (!Array.isArray(observations) || !Number.isFinite(tolerance) || tolerance < 0 || tolerance >= 1 ||
      !Number.isInteger(quorum) || quorum < 2 || observations.length > 15)
    throw new Error('Invalid corroboration inputs');
  const grouped = new Map();
  for (const row of observations) {
    if (!row || typeof row.source !== 'string' || !row.source.trim() ||
        !Number.isFinite(row.value) || row.value <= 0 ||
        (trustLineage && (typeof row.upstream !== 'string' || !row.upstream.trim())))
      throw new Error('Invalid observation or unknown upstream');
    const key = trustLineage ? row.upstream : row.source;
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key).push(row.value);
  }
  const groups = [];
  const quarantined = [];
  for (const [key, values] of grouped) {
    const low = Math.min(...values), high = Math.max(...values);
    if ((high - low) / low > tolerance) { quarantined.push(key); continue; }
    groups.push({key, value: values.reduce((a,b)=>a+b,0)/values.length});
  }
  if (groups.length < quorum) return {status:'abstain', reason:'insufficient_independent_groups', groups:groups.length, quarantined};
  let bestSize = 0, winners = [];
  // Enumerate all pairwise-compatible sets; bridging A~B~C is not transitive.
  for (let mask=1; mask < 2**groups.length; mask++) {
    const chosen = groups.filter((_,i) => mask & (1<<i));
    if (chosen.length < quorum || chosen.length < bestSize) continue;
    const values = chosen.map(g=>g.value);
    if ((Math.max(...values) - Math.min(...values))/Math.min(...values) > tolerance) continue;
    if (chosen.length > bestSize) { bestSize=chosen.length; winners=[]; }
    winners.push(chosen);
  }
  if (!winners.length) return {status:'abstain',reason:'no_quorum',groups:groups.length,quarantined};
  if (winners.length > 1) return {status:'abstain',reason:'ambiguous_equal_quorums',groups:groups.length,quarantined};
  const selected=winners[0];
  return {status:'corroborated_not_verified',value:selected.reduce((a,g)=>a+g.value,0)/selected.length,
    independentGroups:selected.length, groups:groups.length, quarantined};
}

export function benchmark({trials=12000, seed=393, individualFault=0.1, systemicFault=0.03, baseline=2000, amplitude=200, faultMultiplier=1.18}={}) {
  if (!Number.isInteger(trials) || trials < 1 || !Number.isInteger(seed) ||
      individualFault<0 || individualFault>1 || systemicFault<0 || systemicFault>1 ||
      !Number.isFinite(baseline) || !Number.isFinite(amplitude) || baseline<=amplitude || amplitude<0 ||
      !Number.isFinite(faultMultiplier) || faultMultiplier<=0 || Math.abs(faultMultiplier-1)<=0.05) throw Error('Invalid simulation options');
  let state=seed>>>0;
  const rand=()=>{state=(Math.imul(1664525,state)+1013904223)>>>0;return state/4294967296;};
  const methods={naive:{acceptedCorrect:0,acceptedWrong:0,abstained:0},lineage2:{acceptedCorrect:0,acceptedWrong:0,abstained:0},lineage3:{acceptedCorrect:0,acceptedWrong:0,abstained:0}};
  const cases={noFault:0,upstreamOnly:0,systemic:0};
  for (let t=0;t<trials;t++) {
    const trueValue=baseline+amplitude*Math.sin(t/71); // varying baseline, no live prices
    const common=rand()<systemicFault;
    const badA=common||rand()<individualFault;
    const badB=common||rand()<individualFault;
    const badC=common||rand()<individualFault;
    if (common) cases.systemic++;
    else if (badA&&!badB&&!badC) cases.upstreamOnly++;
    else if (!badA&&!badB&&!badC) cases.noFault++;
    const val=bad=>trueValue*(bad?faultMultiplier:1);
    const observations=[
      {source:'mirror-A1',upstream:'A',value:val(badA)},
      {source:'mirror-A2',upstream:'A',value:val(badA)},
      {source:'provider-B',upstream:'B',value:val(badB)},
      {source:'provider-C',upstream:'C',value:val(badC)},
    ];
    for (const [method, options] of Object.entries({
      naive:{trustLineage:false,quorum:2},lineage2:{trustLineage:true,quorum:2},lineage3:{trustLineage:true,quorum:3}})) {
      const result=corroborate(observations,options);
      if (result.status==='abstain') methods[method].abstained++;
      else if (Math.abs(result.value/trueValue-1)>0.05) methods[method].acceptedWrong++;
      else methods[method].acceptedCorrect++;
    }
  }
  return {trials,seed,individualFault,systemicFault,baseline,amplitude,faultMultiplier,cases,methods,
    caution:'Synthetic, independent per-upstream faults plus a common-mode shock. Lineage IDs are assumed correct, not authenticated.'};
}

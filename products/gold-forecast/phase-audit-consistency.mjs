/** Fail closed if a phase breakdown cannot reproduce the pooled audit MAE.
 * Pure checks; no access to raw licensed price history beyond in-memory rows.
 */
export function assertPhaseConsistency(phaseAudit, pooledAudit, horizon) {
  if (!pooledAudit || !phaseAudit || phaseAudit.horizon !== horizon ||
      !Number.isInteger(phaseAudit.n) || phaseAudit.n < 1 ||
      pooledAudit.n !== phaseAudit.n) throw Error('Phase audit count or horizon mismatch');
  const phases=phaseAudit.phases;
  if (!Array.isArray(phases) || phases.length < 1 || phases.length > horizon ||
      phases.some(p => !Number.isInteger(p.n) || p.n < 1 ||
        !Number.isInteger(p.offset) || p.offset < 0 || p.offset >= horizon) ||
      new Set(phases.map(p=>p.offset)).size !== phases.length ||
      phases.reduce((s,p)=>s+p.n,0) !== phaseAudit.n) throw Error('Phase partition mismatch');
  for (const [label,field] of [['baseline','baselineMae'],['priceRidge','priceRidgeMae'],['macroRidge','macroRidgeMae']]) {
    const actual=pooledAudit[label]?.mae;
    const weighted=phases.reduce((s,p)=>s+p.n*p[field],0)/phaseAudit.n;
    if(!Number.isFinite(actual) || !Number.isFinite(weighted) ||
       Math.abs(weighted-actual)>1e-9*Math.max(1,Math.abs(actual)))
      throw Error('Phase MAE does not reconstruct pooled '+label);
  }
  return true;
}

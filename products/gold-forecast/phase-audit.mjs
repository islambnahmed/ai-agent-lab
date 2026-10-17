/** Compare all non-overlapping horizon phases of paired walk-forward predictions.
 * Phase partitions are NOT statistically independent; never cherry-pick offsets.
 */
export function phaseSensitivity(rows,horizon){
  if(!Number.isInteger(horizon)||horizon<1||horizon>30)throw Error('Invalid horizon');
  if(!Array.isArray(rows)||!rows.length)throw Error('Nonempty paired rows required');
  const sorted=[...rows].sort((a,b)=>a.originIndex-b.originIndex),first=sorted[0].originIndex,seen=new Set();
  const groups=Array.from({length:horizon},(_,offset)=>({offset,rows:[]}));
  for(const row of sorted){
    if(!Number.isInteger(row.originIndex)||row.originIndex<first||seen.has(row.originIndex))throw Error('Invalid/duplicate origin');
    seen.add(row.originIndex);
    if(![row.actual,row.originClose,row.pricePoint,row.point].every(Number.isFinite))throw Error('Nonfinite paired row');
    groups[(row.originIndex-first)%horizon].rows.push(row);
  }
  const mae=(rs,key)=>rs.reduce((sum,r)=>sum+Math.abs((key==='baseline'?r.originClose:key==='priceRidge'?r.pricePoint:r.point)-r.actual),0)/rs.length;
  const phases=groups.filter(g=>g.rows.length).map(g=>{
    const baseline=mae(g.rows,'baseline'),price=mae(g.rows,'priceRidge'),macro=mae(g.rows,'macroRidge');
    return {offset:g.offset,n:g.rows.length,baselineMae:baseline,priceRidgeMae:price,macroRidgeMae:macro,
      macroSkillVsPriceRidgePct:price>0?100*(1-macro/price):null,
      macroSkillVsBaselinePct:baseline>0?100*(1-macro/baseline):null};
  });
  const skills=phases.map(p=>p.macroSkillVsPriceRidgePct).filter(Number.isFinite).sort((a,b)=>a-b);
  const pooledPrice=mae(sorted,'priceRidge'),pooledMacro=mae(sorted,'macroRidge');
  return {horizon,n:sorted.length,phaseCount:phases.length,
    macroWinningPhases:phases.filter(p=>p.macroRidgeMae<p.priceRidgeMae).length,
    macroLosingPhases:phases.filter(p=>p.macroRidgeMae>p.priceRidgeMae).length,
    tiedPhases:phases.filter(p=>p.macroRidgeMae===p.priceRidgeMae).length,
    pooledMacroSkillVsPriceRidgePct:pooledPrice>0?100*(1-pooledMacro/pooledPrice):null,
    phaseSkillMinPct:skills[0]??null,phaseSkillMedianPct:skills[Math.floor(skills.length/2)]??null,
    phaseSkillMaxPct:skills.at(-1)??null,phases,
    caveat:'All offsets reported; no post-hoc phase selection. Disjoint horizons are not statistically independent; no predictive-skill claim.'};
}

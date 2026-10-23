/** Phase-rotation audit: all h offsets, not a convenient single non-overlap phase. */
export function auditPhases(candidateRows, baselineRows, horizon) {
  if (!Number.isInteger(horizon) || horizon < 1 || horizon > 365) throw new RangeError('invalid horizon');
  if (!Array.isArray(candidateRows) || !Array.isArray(baselineRows) || !candidateRows.length || candidateRows.length !== baselineRows.length) throw new Error('paired, nonempty rows required');
  const sums = Array.from({length:horizon}, (_,offset)=>({offset,n:0,modelSum:0,baselineSum:0,wins:0,losses:0,ties:0}));
  let totalModel=0,totalBaseline=0;
  for (let i=0;i<candidateRows.length;i++) {
    const c=candidateRows[i], b=baselineRows[i];
    for (const row of [c,b]) if (!row || !Number.isFinite(row.point) || !Number.isFinite(row.actual) || row.actual <= 0) throw new Error('invalid price row');
    if (c.originIndex !== b.originIndex || c.targetDate !== b.targetDate || c.actual !== b.actual) throw new Error('unpaired origins, targets or actuals');
    if (i>0 && c.originIndex<=candidateRows[i-1].originIndex) throw new Error('non-increasing origin index');
    const me=Math.abs(c.point-c.actual), be=Math.abs(b.point-b.actual), phase=sums[i%horizon];
    phase.n++;phase.modelSum+=me;phase.baselineSum+=be;
    if(me<be)phase.wins++;else if(me>be)phase.losses++;else phase.ties++;
    totalModel+=me;totalBaseline+=be;
  }
  const phases=sums.filter(s=>s.n).map(({offset,n,modelSum,baselineSum,wins,losses,ties})=>({
    offset,n,modelMAE:modelSum/n,baselineMAE:baselineSum/n,
    skillPct:baselineSum>0?100*(1-modelSum/baselineSum):null,
    wins,losses,ties
  }));
  const positive=phases.filter(p=>p.skillPct!==null && p.skillPct>0).length;
  const negative=phases.filter(p=>p.skillPct!==null && p.skillPct<0).length;
  const zero=phases.filter(p=>p.skillPct===0).length;
  return {
    horizon,rows:candidateRows.length,
    pooledModelMAE:totalModel/candidateRows.length,
    pooledBaselineMAE:totalBaseline/candidateRows.length,
    pooledSkillPct:totalBaseline>0?100*(1-totalModel/totalBaseline):null,
    phases,phaseSummary:{positive,negative,zero,undefined:phases.length-positive-negative-zero,
      minN:Math.min(...phases.map(p=>p.n)),maxN:Math.max(...phases.map(p=>p.n)),
      label:positive&&negative?'mixed_sign':positive&&!negative?'nonnegative_all_phases':negative&&!positive?'nonpositive_all_phases':'no_direction'},
    caveat:'Overlapping windows share observations. Rotated non-overlap phases are sensitivity slices, not independent replications or a significance test.'
  };
}

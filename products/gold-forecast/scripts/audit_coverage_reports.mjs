// Seshat c296 — audit frozen, real-market retrospective report metadata.
// No live fetches, model changes, or assumption of independent overlapping targets.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

export function auditCoverageReport(report,{label='report',nominalPct=80}={}){
  const horizons=report.priceBenchmarks??report.horizons;
  if(!Array.isArray(horizons)||!horizons.length)throw Error('Missing horizon summaries');
  return {label,source:report.source,from:report.from,to:report.to,rows:report.rows,
    vintageCaveat:'Current-vintage retrospective report, not a prospective forecast score',
    horizons:horizons.map(h=>{
      const n=h.audit?.n,coverage=h.coverage,phases=h.disjoint?.phases;
      if(!Number.isInteger(n)||n<1||!Number.isFinite(coverage)||coverage<0||coverage>100||
         !Array.isArray(phases)||phases.length!==h.horizon)throw Error(`Invalid coverage report for h=${h.horizon}`);
      const total=phases.reduce((s,p)=>s+p.n,0);
      const weighted=phases.reduce((s,p)=>s+p.n*p.coverage/100,0)/n*100;
      if(total!==n||Math.abs(weighted-coverage)>1e-6)throw Error(`Phase/coverage inconsistency for h=${h.horizon}`);
      const disjointN=h.disjoint.candidate?.n;
      if(!Number.isInteger(disjointN)||disjointN<1||disjointN!==phases[0].n)throw Error(`Invalid disjoint count for h=${h.horizon}`);
      const flags=[];
      if(coverage<nominalPct-10)flags.push('historical_coverage_below_nominal_by_over_10pp');
      if(disjointN<10)flags.push('very_small_disjoint_slice');
      else if(disjointN<30)flags.push('small_disjoint_slice');
      if(h.skillPct!==null&&Number.isFinite(h.skillPct)&&h.skillPct<=0)flags.push('no_positive_MAE_skill_vs_persistence');
      return {horizon:h.horizon,model:h.model,auditN:n,coveragePct:coverage,
        nominalPct,nominalGapPp:Number((coverage-nominalPct).toFixed(2)),
        disjointSliceN:disjointN,phaseCount:phases.length,
        phaseCoverageRangePct:[Math.min(...phases.map(p=>p.coverage)),Math.max(...phases.map(p=>p.coverage))],
        maeSkillPct:h.skillPct,flags,
        caveat:'Phase-disjoint target windows can remain dependent; slice N is not an effective independent sample size'};
    })};
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
  const files=[['multi_year_histdata','research-benchmark-20261012.json'],
    ['one_year_standard_bullion','readiness-20261012.json']];
  const audits=files.map(([label,file])=>auditCoverageReport(
    JSON.parse(fs.readFileSync(path.join(root,'reports',file),'utf8')),{label}));
  console.log(JSON.stringify({schemaVersion:1,nominalPct:80,
    warning:'Different sources and periods; comparisons are descriptive, not matched tests. No independence or future coverage guarantee.',
    audits},null,2));
}

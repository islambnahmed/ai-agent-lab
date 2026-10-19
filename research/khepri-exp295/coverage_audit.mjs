// Khepri exp295: source-agnostic retrospective coverage evidence audit.
// No p-values or independent-window claims; historical reports are not blind trials.
import fs from 'node:fs';
function close(a,b,eps=1e-7){return Math.abs(a-b)<=eps;}
function integerHits(n,pct,label){
  if(!Number.isInteger(n)||n<=0||!Number.isFinite(pct)||pct<0||pct>100)
    throw Error(`${label}: invalid count or coverage`);
  const hits=Math.round(n*pct/100);
  if(!close(hits*100/n,pct))throw Error(`${label}: percentage cannot represent an integer count`);
  return hits;
}
export function auditReport(report,{target=0.8,minPhaseN=10,phaseFraction=0.9}={}){
  if(!report||!Number.isFinite(target)||target<=0||target>=1||!Number.isInteger(minPhaseN)||minPhaseN<1||!Number.isFinite(phaseFraction)||phaseFraction<=0||phaseFraction>1)
    throw Error('Invalid report or audit configuration');
  const horizons=report.priceBenchmarks??report.horizons;
  if(!Array.isArray(horizons)||!horizons.length)throw Error('Missing forecast horizons');
  const seen=new Set();
  const results=horizons.map(row=>{
    const h=row.horizon,n=row.audit?.n,phases=row.disjoint?.phases;
    if(![1,7,30].includes(h)||seen.has(h)||!Array.isArray(phases)||phases.length!==h)throw Error('Invalid or duplicate horizon/phase partition');
    seen.add(h);
    const hits=integerHits(n,row.coverage,`h${h}`);
    let phaseN=0,phaseHits=0,below=0,adequate=0;
    for(let i=0;i<phases.length;i++){
      const phase=phases[i];
      if(phase.offset!==i)throw Error('Phase offsets must be ordered and complete');
      const successes=integerHits(phase.n,phase.coverage,`h${h} phase${i}`);
      phaseN+=phase.n;phaseHits+=successes;
      if(phase.coverage/100<target)below++;
      if(phase.n>=minPhaseN)adequate++;
    }
    if(phaseN!==n||phaseHits!==hits)throw Error(`h${h}: phase/aggregate coverage mismatch`);
    const miss=n-hits,expectedMiss=(1-target)*n,enough=adequate===h;
    return {horizon:h,n,hits,misses:miss,coveragePct:row.coverage,nominalPct:100*target,
      excessMissesVsNominal:miss-expectedMiss,phaseBelow:below,phaseCount:h,
      phaseMinN:Math.min(...phases.map(x=>x.n)),phaseEvidenceAdequate:enough,
      broadPhaseShortfall:enough&&below/h>=phaseFraction&&row.coverage/100<target,
      origin:row.auditedFrom??null,
      caveat:'Descriptive retrospective audit only; phase offsets share market shocks and are not independent. No prospective skill or statistical significance established.'};
  });
  return {source:report.source??'unlabeled',rows:report.rows??null,period:[report.from??null,report.to??null],results};
}
if(process.argv[1]&&import.meta.url===`file://${process.argv[1]}`){
  if(process.argv.length<3)throw Error('Usage: node coverage_audit.mjs REPORT.json [REPORT2.json ...]');
  const output=process.argv.slice(2).map(f=>auditReport(JSON.parse(fs.readFileSync(f,'utf8'))));
  process.stdout.write(JSON.stringify(output,null,2)+'\n');
}

// Worker A research-only phase audit: never promotes a model or fetches market data.
// Usage: node experiments/worker_a/phase_audit.mjs <readiness.json> [research-benchmark.json]
import fs from 'node:fs';

export function auditPhases(report) {
  const groups=Array.isArray(report.horizons)?report.horizons:report.priceBenchmarks;
  if(!Array.isArray(groups)||groups.length===0)throw Error("Missing horizon groups");
  return groups.map(group=>{
    const h=group.horizon,n=group.audit?.n,phases=group.disjoint?.phases;
    if(!Number.isInteger(h)||h<1||!Number.isInteger(n)||n<1||!Array.isArray(phases)||phases.length!==Math.min(h,n))throw Error("Invalid horizon/phase count");
    let count=0,covered=0;
    for(let i=0;i<phases.length;i++){
      const p=phases[i];
      if(p.offset!==i||!Number.isInteger(p.n)||p.n<1||!Number.isFinite(p.coverage)||p.coverage<0||p.coverage>100)throw Error("Invalid phase");
      const k=p.n*p.coverage/100;
      if(Math.abs(k-Math.round(k))>1e-7)throw Error("Nonintegral phase coverage count");
      count+=p.n;covered+=Math.round(k);
    }
    if(count!==n||!Number.isFinite(group.coverage)||Math.abs(100*covered/n-group.coverage)>1e-7)throw Error("Phase totals inconsistent with audit");
    const values=phases.map(p=>p.coverage),sizes=phases.map(p=>p.n),min=Math.min(...values),max=Math.max(...values);
    return {horizon:h,model:group.model,n,covered,coveragePct:100*covered/n,phaseCount:phases.length,phaseMinPct:min,phaseMaxPct:max,phaseSpreadPp:max-min,phaseMinN:Math.min(...sizes),phaseMaxN:Math.max(...sizes),zeroPctPhases:values.filter(v=>v===0).length,fullPctPhases:values.filter(v=>v===100).length,smallPhaseWarning:Math.min(...sizes)<5,sourceVintageCaveat:"Retrospective overlapping windows; phase selection is descriptive, not independent evidence."};
  });
}

if (process.argv[1]?.endsWith('/phase_audit.mjs')) {
  const paths=process.argv.slice(2);
  if(!paths.length)throw Error('Provide report JSON paths');
  for(const path of paths){
    const report=JSON.parse(fs.readFileSync(path,'utf8'));
    console.log(JSON.stringify({path,results:auditPhases(report)},null,2));
  }
}

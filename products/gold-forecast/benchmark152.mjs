import {auditDependence} from './audit_dependence.mjs';
import fs from 'node:fs';

function random(seed){let x=seed>>>0;return ()=>{x=(Math.imul(x,1664525)+1013904223)>>>0;return (x+.5)/4294967296}}
function series(seed,domain,n=260){
  const rng=random(seed),rows=[];let p=domain==='gold'?2400:150;
  for(let i=0;i<n;i++){
    // Synthetic: regimes and autocorrelation; intentionally NOT calibrated to market data.
    const u=Math.max(1e-12,rng()),v=rng();
    const z=Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*v);
    const regime=(i>n*.79 && seed%3===0)?3.5:1;
    const sigma=(domain==='gold'?.009:.04)*regime;
    const seasonal=domain==='seo'?0.002*Math.sin(i*.4):0;
    p=Math.max(.1,p*Math.exp(sigma*z+(domain==='gold'?.0002:.001)+seasonal));
    rows.push({date:new Date(Date.UTC(2024,0,1+i)).toISOString().slice(0,10),price:p});
  }
  return rows;
}
const summary={experiment:152,fixture:'deterministic synthetic log-price walks, 260 daily rows, seed 1..160 per domain',byDomain:{}};
for(const domain of ['gold','seo']){
  summary.byDomain[domain]={};
  for(const h of [1,7,30]){
    let valid=0, mixed=0, spans100=0, claimed80=0,claimed80Underpowered=0,beat=0,beatUnderpowered=0;
    let maxDisjoint=null,nAudit=null;let sumCoverage=0;
    for(let seed=1;seed<=160;seed++){
      const r=auditDependence(series(seed,domain),h);
      valid++;if(r.beatBaselineOnAudit){beat++;if(r.auditInterpretation==='descriptive_only')beatUnderpowered++}maxDisjoint=r.maxDisjointTargetWindows;nAudit=r.nAudit;
      if(r.phaseCoverageMin<r.phaseCoverageMax)mixed++;
      if(r.phaseCoverageMax-r.phaseCoverageMin===100)spans100++;
      if(r.literalCoverage>=80){claimed80++;if(r.auditInterpretation==='descriptive_only')claimed80Underpowered++}
      sumCoverage+=r.literalCoverage;
    }
    summary.byDomain[domain][h]={valid,nAudit,maxDisjoint,mixedPhaseCoverage:mixed,phaseRangeFull100:spans100,
      literalCoverageAtLeast80:claimed80,beatBaselineOnAudit:beat,beatButDescriptive:beatUnderpowered,atLeast80ButDescriptive:claimed80Underpowered,
      meanLiteralCoverage:sumCoverage/valid};
  }
}
fs.writeFileSync(new URL('./results152.json',import.meta.url),JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify(summary,null,2));

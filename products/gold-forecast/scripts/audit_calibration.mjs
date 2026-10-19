// Reproducible descriptive coverage audit for committed Gold Lab reports.
// Does not claim independent trials, conformal validity, or future coverage.
import fs from 'node:fs';

const HORIZONS=[1,7,30];
function assert(ok,message){if(!ok)throw Error(message);}
function count(n,pct,label){
  assert(Number.isInteger(n)&&n>0,`${label}: invalid n`);
  assert(typeof pct==='number'&&Number.isFinite(pct)&&pct>=0&&pct<=100,`${label}: invalid coverage`);
  const hits=Math.round(n*pct/100);
  assert(Math.abs(100*hits/n-pct)<1e-7,`${label}: percentage cannot represent an integer hit count`);
  return hits;
}
export function auditReport(report,name){
  assert(report&&typeof report==='object',`${name}: invalid report`);
  const rows=report.priceBenchmarks??report.horizons;
  assert(Array.isArray(rows),`${name}: no benchmark rows`);
  const seen=new Set();
  const horizons=rows.map(row=>{
    const h=row.horizon;
    assert(HORIZONS.includes(h)&&!seen.has(h),`${name}: duplicate/unsupported horizon`);seen.add(h);
    const n=row.audit?.n, hits=count(n,row.coverage,`${name}/h${h}`);
    const phases=row.disjoint?.phases;
    assert(Array.isArray(phases)&&phases.length===h,`${name}/h${h}: missing phases`);
    let phaseN=0,phaseHits=0;
    for(const p of phases){
      phaseN+=p.n;
      phaseHits+=count(p.n,p.coverage,`${name}/h${h}/phase${p.offset}`);
    }
    assert(phaseN===n&&phaseHits===hits,`${name}/h${h}: phase totals disagree with aggregate`);
    assert(Number.isInteger(row.calibration?.n)&&row.calibration.n>0,`${name}/h${h}: invalid calibration n`);
    return {horizon:h,model:row.model,calibrationN:row.calibration.n,auditN:n,inside:hits,
      outside:n-hits,coveragePct:row.coverage,nominalPct:80,gapPp:row.coverage-80,
      phaseCoverageMinPct:Math.min(...phases.map(p=>p.coverage)),
      phaseCoverageMaxPct:Math.max(...phases.map(p=>p.coverage)),
      descriptiveFlag:row.coverage<80?'below_80_in_this_audit':'at_or_above_80_in_this_audit'};
  });
  assert(seen.size===HORIZONS.length,`${name}: missing horizon`);
  const end=Date.parse(report.to+'T00:00:00Z'),run=Date.parse(report.runAt);
  assert(Number.isFinite(end)&&Number.isFinite(run),`${name}: missing report dates`);
  return {name,runAt:report.runAt,lastPriceDate:report.to,
    dataEndLagDays:Math.floor((run-end)/86400000),
    source:report.source,calendar:report.calendar,horizons};
}
export function compareReports(reports){
  assert(Array.isArray(reports)&&reports.length===2,'Need two reports');
  const [a,b]=reports;
  return HORIZONS.map(h=>{
    const x=a.horizons.find(v=>v.horizon===h),y=b.horizons.find(v=>v.horizon===h);
    return {horizon:h,coverageDifferencePp:y.coveragePct-x.coveragePct,
      sameModel:x.model===y.model,models:[x.model,y.model],
      caveat:'Descriptive only: periods, sources, sample sizes, calibration windows and potentially models differ.'};
  });
}
if(process.argv[1]&&import.meta.url===new URL('file://'+process.argv[1]).href){
  const paths=process.argv.slice(2);
  assert(paths.length===2,'Usage: node audit_calibration.mjs RESEARCH_REPORT.json READINESS_REPORT.json');
  const reports=paths.map(p=>auditReport(JSON.parse(fs.readFileSync(p,'utf8')),p));
  process.stdout.write(JSON.stringify({reports,comparisons:compareReports(reports),
    caveat:'Retrospective descriptive audit only; overlapping horizons, time dependence, different vintages and prior inspection invalidate naive independent-trial significance or forward-coverage claims.'},null,2)+'\n');
}

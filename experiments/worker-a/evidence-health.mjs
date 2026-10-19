/** Report-only evidence health check; does not alter forecasts or certify skill. */
import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const round=x=>Math.round(x*100)/100;
const day=s=>{
  if(typeof s!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(s))throw Error('Invalid ISO day');
  const t=Date.parse(s+'T00:00:00Z');
  if(!Number.isFinite(t)||new Date(t).toISOString().slice(0,10)!==s)throw Error('Invalid calendar day');
  return t;
};
export function summarizeReport(report,{asOf='2026-10-19',minPhaseN=10,targetCoveragePct=80}={}){
  if(!report||typeof report!=='object')throw TypeError('Report must be an object');
  if(!Number.isInteger(minPhaseN)||minPhaseN<1)throw RangeError('Invalid minimum phase sample size');
  if(!finite(targetCoveragePct)||targetCoveragePct<=0||targetCoveragePct>=100)throw RangeError('Invalid target coverage');
  const asOfMs=day(asOf),lastMs=day(report.to);
  if(asOfMs<lastMs)throw Error('asOf precedes report latest observation');
  const horizons=report.priceBenchmarks??report.horizons;
  if(!Array.isArray(horizons)||!horizons.length)throw Error('Missing horizon reports');
  const seen=new Set();
  return {
    reportRunAt:report.runAt??null,source:report.source,
    measurement:report.measurement??'source-defined provider close',
    observedThrough:report.to,observationAgeDays:Math.round((asOfMs-lastMs)/86400000),asOf,
    horizonSummaries:horizons.map(h=>{
      const k=h.horizon,phases=h.disjoint?.phases;
      if(!Number.isInteger(k)||k<1||seen.has(k))throw Error('Invalid or duplicate horizon');
      seen.add(k);
      if(!Array.isArray(phases)||phases.length!==k)throw Error('Missing phase coverage for horizon '+k);
      if(!Number.isInteger(h.audit?.n)||h.audit.n<1||!finite(h.coverage)||!finite(h.audit?.mae)||!finite(h.baseline?.mae))throw Error('Invalid audit summary');
      const offsets=new Set();let n=0,covered=0;
      for(const p of phases){
        if(!Number.isInteger(p.offset)||p.offset<0||p.offset>=k||offsets.has(p.offset)||
          !Number.isInteger(p.n)||p.n<1||!finite(p.coverage)||p.coverage<0||p.coverage>100)throw Error('Invalid phase');
        offsets.add(p.offset);n+=p.n;covered+=p.n*p.coverage/100;
      }
      if(n!==h.audit.n)throw Error('Phase counts do not sum to audit n for horizon '+k);
      if(Math.abs(100*covered/n-h.coverage)>0.00001)throw Error('Phase coverage inconsistent for horizon '+k);
      const minN=Math.min(...phases.map(p=>p.n));
      const minCov=Math.min(...phases.map(p=>p.coverage));
      const maxCov=Math.max(...phases.map(p=>p.coverage));
      const small=phases.filter(p=>p.n<minPhaseN).length;
      const skill=h.baseline.mae>0?100*(1-h.audit.mae/h.baseline.mae):null;
      if(finite(h.skillPct)&&skill!==null&&Math.abs(h.skillPct-skill)>0.001)throw Error('Reported skill disagrees with audit MAE');
      return {
        horizon:k,selectedModel:h.model,auditN:n,auditCoveragePct:round(h.coverage),
        targetCoveragePct,coverageShortfallPoints:round(targetCoveragePct-h.coverage),
        phaseCoverageRangePct:[round(minCov),round(maxCov)],phaseSpreadPoints:round(maxCov-minCov),
        phaseMinN:minN,phaseMaxN:Math.max(...phases.map(p=>p.n)),
        phaseCoverageStepAtMinNPoints:round(100/minN),phasesBelowMinN:small,phasesTotal:k,
        phaseEvidenceStatus:small===k?'ALL_PHASES_SMALL':small?'SOME_PHASES_SMALL':'PHASE_COUNTS_REPORTED',
        skillVsPersistencePct:skill===null?null:round(skill),
        caveat:'Phase coverage is not phase MAE skill; windows may remain dependent. No prospective skill claim.'
      };
    })
  };
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
  const [path,asOf='2026-10-19']=process.argv.slice(2);
  if(!path){console.error('Usage: node evidence-health.mjs <saved-report.json> [YYYY-MM-DD]');process.exitCode=2;}
  else try{console.log(JSON.stringify(summarizeReport(JSON.parse(readFileSync(path,'utf8')),{asOf}),null,2));}
  catch(err){console.error(err.message);process.exitCode=1;}
}

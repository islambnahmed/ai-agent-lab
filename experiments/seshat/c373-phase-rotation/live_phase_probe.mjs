/** Read-only empirical phase sensitivity probe. Only derived metrics go to CI logs. */
import {createHash} from 'node:crypto';
import {forecast} from '../../../products/gold-forecast/forecast.mjs';
import {prepareProviderHistory} from '../../../products/gold-forecast/data.mjs';
import {auditPhases} from './phase_metrics.mjs';

async function main(){
  const url='https://standardbullion.com/api/v1/market/history?metal=XAU&range=1y';
  const res=await fetch(url,{signal:AbortSignal.timeout(30000),headers:{Accept:'application/json'}});
  if(!res.ok)throw Error('provider HTTP '+res.status);
  const raw=Buffer.from(await res.arrayBuffer());
  if(!raw.length||raw.length>5_000_000)throw Error('invalid response length');
  const receivedAt=new Date().toISOString();
  const rawSha256=createHash('sha256').update(raw).digest('hex');
  const payload=JSON.parse(raw.toString('utf8'));
  const prepared=prepareProviderHistory(payload,receivedAt);
  const results=[1,7,30].map(h=>{
    const f=forecast(prepared.series,h,{asOf:receivedAt,includeRows:true});
    const phase=auditPhases(f.rows.audit,f.rows.baseline,h);
    return {horizon:h,model:f.model,sourceVintagePooledSkillPct:f.skillPct,
      ...phase,allPhaseOffsetsReported:true};
  });
  console.log(JSON.stringify({experiment:'seshat-c373-rotated-phase-audit',status:'current_vintage_descriptive_only',
    fetchedAt:receivedAt,provider:'Standard Bullion',sourceUrl:url,rawSha256,
    observations:prepared.series.length,from:prepared.series[0].date,to:prepared.series.at(-1).date,
    cadence:prepared.calendar,results,
    limitations:['No original 2026-10-12 source vintage is reconstructed',
      'Current feed is mutable and not independently validated',
      'Historical audit data were previously inspected; no blind model skill claim',
      'Non-overlapping targets remain dependent through shared market regime',
      'This is a descriptive sensitivity check, not a prospective forecast outcome']},null,2));
}
main().catch(err=>{console.error('PHASE_PROBE_FAILED:',err.message);process.exitCode=2;});

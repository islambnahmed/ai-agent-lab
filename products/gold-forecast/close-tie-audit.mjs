/**
 * Seshat cycle 230: diagnose exact repeated XAU closes without labeling them
 * as errors. Input must be a validated, chronologically sorted daily series.
 * No prices are included in output; dates alone cannot establish market cause.
 */
import {createHash} from 'node:crypto';
const DAYS=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
const DAY_MS=86400000;

function validatedDates(series){
  if(!Array.isArray(series)||series.length<2)throw new TypeError('At least two closes required');
  let previous=-Infinity;
  return series.map((row,i)=>{
    if(!row||typeof row.date!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(row.date))
      throw new TypeError('Expected YYYY-MM-DD dates');
    const ms=Date.parse(row.date+'T00:00:00Z');
    if(!Number.isFinite(ms)||new Date(ms).toISOString().slice(0,10)!==row.date||ms<=previous)
      throw new RangeError('Dates must be valid, unique and strictly increasing');
    if(typeof row.price!=='number'||!Number.isFinite(row.price)||row.price<=0)
      throw new TypeError('Finite positive numeric prices required');
    previous=ms;
    return ms;
  });
}

/** firstTargetIndex is inclusive, endTargetIndex exclusive; a tie compares
 * each target against its immediately preceding observed provider close.
 */
export function auditCloseTies(series,{firstTargetIndex=1,endTargetIndex=series?.length}={}){
  const dates=validatedDates(series);
  if(!Number.isInteger(firstTargetIndex)||!Number.isInteger(endTargetIndex)||
     firstTargetIndex<1||endTargetIndex>series.length||endTargetIndex<=firstTargetIndex)
    throw new RangeError('Nonempty valid target-index window required');
  const targets=endTargetIndex-firstTargetIndex;
  const byTargetWeekday=Object.fromEntries(DAYS.map(d=>[d,{observations:0,ties:0}]));
  const ties=[];
  let weekendTargetTies=0,weekdayTargetTies=0,acrossGapTies=0,consecutiveDayTies=0;
  const runs=[];
  let run=null;
  const flush=()=>{if(run){runs.push(run);run=null;}};
  for(let i=firstTargetIndex;i<endTargetIndex;i++){
    const weekday=DAYS[new Date(dates[i]).getUTCDay()];
    const gapDays=(dates[i]-dates[i-1])/DAY_MS;
    byTargetWeekday[weekday].observations++;
    if(series[i].price!==series[i-1].price){flush();continue;}
    byTargetWeekday[weekday].ties++;
    const weekend=weekday==='Saturday'||weekday==='Sunday';
    if(weekend)weekendTargetTies++;else weekdayTargetTies++;
    if(gapDays>1)acrossGapTies++;else consecutiveDayTies++;
    ties.push({originDate:series[i-1].date,targetDate:series[i].date,targetWeekday:weekday,gapDays});
    if(!run){run={firstDate:series[i-1].date,lastDate:series[i].date,observedCloses:2,ties:1,maxGapDays:gapDays};}
    else {run.lastDate=series[i].date;run.observedCloses++;run.ties++;run.maxGapDays=Math.max(run.maxGapDays,gapDays);}
  }
  flush();
  return {targets,exactTies:ties.length,exactTiePct:100*ties.length/targets,
    weekendTargetTies,weekdayTargetTies,acrossGapTies,consecutiveDayTies,
    byTargetWeekday,runs,ties,
    interpretation:'Exact repeats may reflect true unchanged quotes, market closures, vendor carry-forward or precision. This diagnostic cannot identify cause.'};
}

/** Reconstruct the horizon=1 validation and audit origin windows from the
 * frozen readiness report, only if the original series hash matches exactly.
 */
export function reconcileReadinessTies(report,series){
  validatedDates(series);
  if(report?.schemaVersion!==1||report.rows!==series.length||
     report.historyHash!==createHash('sha256').update(JSON.stringify(series)).digest('hex'))
    throw new Error('Historical snapshot hash/length mismatch: cannot attribute published results');
  const h=report.horizons?.find(x=>x.horizon===1);
  const p=h?.candidates?.find(x=>x.model==='persistence')?.validation;
  if(!p||h.baseline?.n!==series.length-h.split?.auditStart||
     !Number.isInteger(h.split.selectionEnd)||!Number.isInteger(h.split.auditStart)||
     !Number.isInteger(p.n)||p.n<1)
    throw new Error('Missing or inconsistent one-close report windows');
  const validation=auditCloseTies(series,{firstTargetIndex:h.split.selectionEnd-p.n,endTargetIndex:h.split.selectionEnd});
  const audit=auditCloseTies(series,{firstTargetIndex:h.split.auditStart,endTargetIndex:series.length});
  for(const [name,result,metric] of [['validation',validation,p],['audit',audit,h.baseline]]){
    if(result.targets!==metric.n||Math.abs(result.exactTiePct-metric.directionAccuracy)>1e-8)
      throw new Error(name+' legacy direction percentage does not match exact close ties');
  }
  return {source:report.source,asOf:report.asOf,historyHash:report.historyHash,
    validation,audit,verifiedAgainstPublishedPersistenceDirectionAccuracy:true,
    caveat:'Matching a stored history hash checks equality to the frozen report, not external provider authenticity or why closes repeat.'};
}

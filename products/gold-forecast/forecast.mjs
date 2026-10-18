import {prepareHistory,targetDate} from './data.mjs';
import {predict,MODEL_NAMES,MODEL_VERSION} from './models.mjs';
export {predict,MODEL_NAMES,MODEL_VERSION};

// Kept for external exploratory consumers; production forecasts use the strict
// historical-integrity adapter instead of silently cleaning malformed prices.
export function normalize(raw,{asOf=new Date()}={}){
  if(!Array.isArray(raw))throw Error('Invalid price series');
  const valid=raw.filter(r=>r&&Number.isFinite(Number(r.price??r.close))&&Number(r.price??r.close)>0&&typeof(r.date??r.t)==='string');
  const days=new Map();
  for(const row of valid){
    const stamp=row.t??row.date;
    if(!/^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))?$/.test(stamp))continue;
    const ts=Date.parse(stamp),day=stamp.slice(0,10);
    if(!Number.isFinite(ts)||new Date(day+'T00:00:00Z').toISOString().slice(0,10)!==day)continue;
    if(ts>new Date(asOf).valueOf())throw Error('Future-dated historical price');
    const utc=new Date(ts).toISOString().slice(0,10),old=days.get(utc);
    if(!old||ts>=old.ts)days.set(utc,{date:utc,price:Number(row.price??row.close),ts});
  }
  return [...days.values()].sort((a,b)=>a.date.localeCompare(b.date)).map(({date,price})=>({date,price}));
}
const mean=xs=>xs.reduce((a,b)=>a+b,0)/xs.length;
export function metrics(rows){
  if(!rows.length)throw Error('No evaluation rows');
  // A zero-return forecast (notably persistence) makes no directional call.
  // Report conditional hit rate and participation separately, not false 0% accuracy.
  const active=rows.filter(r=>Math.sign(r.point-r.originClose)!==0);
  return {n:rows.length,mae:mean(rows.map(r=>Math.abs(r.point-r.actual))),
    rmse:Math.sqrt(mean(rows.map(r=>(r.point-r.actual)**2))),
    mape:100*mean(rows.map(r=>Math.abs(r.point-r.actual)/r.actual)),
    directionAccuracy:active.length?100*mean(active.map(r=>Math.sign(r.point-r.originClose)===Math.sign(r.actual-r.originClose)?1:0)):null,
    directionalPredictions:active.length,
    directionalAbstentions:rows.length-active.length,
    directionalCoveragePct:100*active.length/rows.length};
}
export function sample(series,h,model,start,end,stride=1){
  const prices=series.map(r=>r.price),rows=[];
  for(let i=start;i<end;i+=stride){
    const point=predict(prices.slice(0,i),h,model),actual=prices[i+h-1];
    rows.push({originIndex:i-1,originDate:series[i-1].date,targetDate:series[i+h-1].date,
      originClose:prices[i-1],point,actual,bandError:Math.abs(point-actual)/point});
  }
  return rows;
}
function calibrationBand(rows){
  const errors=rows.map(r=>r.bandError).sort((a,b)=>a-b);
  // Finite-sample order statistic; no iid/conformal coverage guarantee claimed.
  const rank=Math.min(errors.length,Math.ceil((errors.length+1)*0.8));
  return Math.max(0.002,errors[rank-1]);
}
export function forecast(raw,h=7,{asOf=new Date().toISOString(),includeRows=false}={}){
  if(![1,7,30].includes(h))throw Error('Unsupported horizon');
  const data=prepareHistory(raw,{asOf,minRows:h===30?240:165});
  const series=data.series,n=series.length,prices=series.map(r=>r.price);
  const selectionEnd=Math.floor(n*0.6),auditStart=Math.floor(n*0.8);
  // Targets for selection, calibration and audit occupy separate periods.
  // Purge h-1 origins at each boundary so future labels cannot leak back.
  const candidates=Object.keys(MODEL_NAMES).map(model=>{
    const rows=sample(series,h,model,65,selectionEnd-h+1);
    return {model,validation:metrics(rows)};
  }).sort((a,b)=>a.validation.mae-b.validation.mae);
  const model=candidates[0].model;
  const calibrationRows=sample(series,h,model,selectionEnd,auditStart-h+1);
  const auditRows=sample(series,h,model,auditStart,n-h+1);
  const baselineRows=sample(series,h,'persistence',auditStart,n-h+1);
  if(calibrationRows.length<10||auditRows.length<10)throw Error('Need 10 calibration and 10 audit targets');
  const band=calibrationBand(calibrationRows),point=predict(prices,h,model);
  const audit=metrics(auditRows),baseline=metrics(baselineRows);
  const disjointRows=auditRows.filter((_,i)=>i%h===0),disjointBase=baselineRows.filter((_,i)=>i%h===0);
  const phases=Array.from({length:h},(_,offset)=>{
    const rows=auditRows.filter((_,i)=>i%h===offset);
    return rows.length?{offset,n:rows.length,coverage:100*mean(rows.map(r=>r.bandError<=band?1:0))}:null;
  }).filter(Boolean);
  const result={version:MODEL_VERSION,model,horizon:h,horizonUnit:'future observed provider closes',calendar:data.calendar,
    targetDate:data.calendar==='observations'?null:targetDate(series.at(-1).date,h,data.calendar),
    point,lower:Math.max(0,point*(1-band)),upper:point*(1+band),band,
    coverage:100*mean(auditRows.map(r=>r.bandError<=band?1:0)),
    audit,baseline,beat:audit.mae<baseline.mae,
    skillPct:baseline.mae>0?100*(1-audit.mae/baseline.mae):null,
    candidates,calibration:{n:calibrationRows.length,from:series[selectionEnd].date,to:series[auditStart-1].date},
    disjoint:{candidate:metrics(disjointRows),baseline:metrics(disjointBase),phases,
      caveat:'Non-overlapping target windows are not statistically independent'},
    split:{selectionEnd,auditStart,purgedOriginsPerBoundary:h-1},
    series:series.slice(-120),latest:series.at(-1),auditedFrom:series[auditStart].date,
    dataQuality:{rows:n,excludedSameDay:data.excludedSameDay,ageDays:data.ageDays,warnings:data.warnings},
    evidence:'Retrospective reconstruction from current data vintage; prospective skill is unproven'};
  if(includeRows)result.rows={calibration:calibrationRows,audit:auditRows,baseline:baselineRows};
  return result;
}
export function tradingDate(dateISO,h){return targetDate(dateISO,h,'weekdays');}

// Three-way chronological selection/calibration/audit prototype.
// Calibration is descriptive; this is NOT an independence or coverage guarantee.
import {MODEL_NAMES,normalize,predict} from './forecast.mjs';
import {calibrateMultiplicativeInterval,intervalAt,empiricalCoverage} from './calibration.mjs';

const mean=xs=>xs.reduce((s,x)=>s+x,0)/xs.length;
function paired(prices,h,model,start,end,stride){
  const pairs=[];
  for(let i=start;i<end;i+=stride){
    if(i+h-1>=prices.length)break;
    pairs.push({origin:i,predicted:predict(prices.slice(0,i),h,model),actual:prices[i+h-1]});
  }
  return pairs;
}
function metrics(pairs){
  return {n:pairs.length,mae:mean(pairs.map(p=>Math.abs(p.predicted-p.actual))),
    mape:100*mean(pairs.map(p=>Math.abs(p.predicted-p.actual)/p.actual))};
}
function countDisjoint(pairs,h){
  let count=0,lastTarget=-1;
  for(const p of pairs){
    if(p.origin>lastTarget){count++;lastTarget=p.origin+h-1;}
  }
  return count;
}
export function honestForecast(raw,h=7,{selectionFraction=0.55,auditFraction=0.8}={}){
  if(![1,7,30].includes(h))throw Error('Unsupported horizon');
  if(!(selectionFraction>0&&selectionFraction<auditFraction&&auditFraction<1))throw Error('Invalid chronological split');
  const series=normalize(raw),prices=series.map(p=>p.price),n=prices.length;
  if(n<165)throw Error('Not enough price history');
  const selectionEnd=Math.floor(n*selectionFraction),auditStart=Math.floor(n*auditFraction);
  const validationStart=Math.max(65,2*h+45),stride=Math.max(1,Math.floor(h/5));
  const selectionCandidates=Object.keys(MODEL_NAMES).map(model=>({
    model,pairs:paired(prices,h,model,validationStart,selectionEnd-h+1,stride)
  }));
  if(selectionCandidates.some(c=>c.pairs.length<10))throw Error('Insufficient selection evidence');
  const scored=selectionCandidates.map(c=>({...c,score:metrics(c.pairs).mae}));
  scored.sort((a,b)=>a.score-b.score);
  const chosen=scored[0].model;
  // Model is frozen before the calibration window.
  const calibration=paired(prices,h,chosen,selectionEnd,auditStart-h+1,stride);
  const audit=paired(prices,h,chosen,auditStart,n-h+1,1);
  const baseline=paired(prices,h,'persistence',auditStart,n-h+1,1);
  if(calibration.length<10)throw Error('Insufficient calibration evidence');
  if(audit.length<10)throw Error('Insufficient audit evidence');
  const {logRadius,band}=calibrateMultiplicativeInterval(calibration);
  const point=predict(prices,h,chosen),interval=intervalAt(point,logRadius);
  const auditMetrics=metrics(audit),baselineMetrics=metrics(baseline);
  return {model:chosen,point,...interval,band,logRadius,
    coverage:empiricalCoverage(audit,logRadius),audit:auditMetrics,baseline:baselineMetrics,
    beat:auditMetrics.mae<baselineMetrics.mae,
    latest:series.at(-1),auditedFrom:series[auditStart].date,
    calibrationCount:calibration.length,calibrationDisjointWindows:countDisjoint(calibration,h),
    auditDisjointWindows:countDisjoint(audit,h),
    selectionCount:scored[0].pairs.length,
    coverageStatus:countDisjoint(audit,h)>=20?'descriptive_only_even_with_20_disjoint_windows':'insufficient_disjoint_audit_windows',
    selectionEndDate:series[selectionEnd-1].date,
    calibrationEndDate:series[auditStart-1].date,
    warning:'Descriptive only; disjoint target windows are not statistically independent. Calibration/model selection are separated but temporal dependence and regime shifts remain.'};
}

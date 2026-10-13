/** Fixed-clock 75m gold backtest audit. Retrospective only, not live evidence.
 * Issue anchors do NOT move when market quotes are missing.
 * Input rows must be sorted {t, price, source} observations at actual availability times.
 */
export const MIN=60_000;
export const HORIZON=75*MIN;
const findBefore=(rows,t)=>{let lo=0,hi=rows.length;while(lo<hi){const m=(lo+hi)>>>1;if(rows[m].t<=t)lo=m+1;else hi=m;}return lo-1;};
const findAfter=(rows,t)=>{let lo=0,hi=rows.length;while(lo<hi){const m=(lo+hi)>>>1;if(rows[m].t<t)lo=m+1;else hi=m;}return lo;};
const metrics=a=>({n:a.length,mae:a.length?a.reduce((s,x)=>s+x,0)/a.length:null,
 rmse:a.length?Math.sqrt(a.reduce((s,x)=>s+x*x,0)/a.length):null});
export function evaluateFixedGrid(rows,{startMs,endMs,asOfMs,strideMs=HORIZON,
 maxIssueLagMs=2*MIN,maxLookbackLagMs=5*MIN,maxTargetLagMs=10*MIN}={}){
 if(!Array.isArray(rows)||!rows.length)throw Error('Observations required');
 let last=-Infinity,src;
 for(const r of rows){if(!r||!Number.isSafeInteger(r.t)||r.t<=last||!Number.isFinite(r.price)||r.price<=0||
  typeof r.source!=='string'||!r.source||(src!==undefined&&src!==r.source))throw Error('Invalid ordered observations');
  last=r.t;src=r.source;}
 if(![startMs,endMs,asOfMs,strideMs,maxIssueLagMs,maxLookbackLagMs,maxTargetLagMs].every(Number.isSafeInteger)||
  endMs<startMs||endMs>asOfMs||strideMs<MIN||maxIssueLagMs<0||maxLookbackLagMs<0||maxTargetLagMs<0||
  Math.floor((endMs-startMs)/strideMs)>100_000)throw Error('Invalid fixed grid');
 const out={source:src,firstAnchor:new Date(startMs).toISOString(),lastAnchor:new Date(endMs).toISOString(),
  asOf:new Date(asOfMs).toISOString(),scheduled:0,eligible:0,missingIssue:0,missingLookback:0,
  invalidMomentum:0,notMatured:0,matured:0,missingTarget:0,evaluated:0};
 const p=[],m=[];
 for(let t=startMs;t<=endMs;t+=strideMs){
  out.scheduled++;
  const i=findBefore(rows,t);
  if(i<0||t-rows[i].t>maxIssueLagMs){out.missingIssue++;continue;}
  const j=findBefore(rows,t-30*MIN);
  if(j<0||t-30*MIN-rows[j].t>maxLookbackLagMs){out.missingLookback++;continue;}
  const rate=(rows[i].price-rows[j].price)/(rows[i].t-rows[j].t);
  const prediction=rows[i].price+rate*(t+HORIZON-rows[i].t);
  if(!Number.isFinite(prediction)||prediction<=0){out.invalidMomentum++;continue;}
  out.eligible++;
  const target=t+HORIZON;
  if(target>asOfMs){out.notMatured++;continue;}
  out.matured++;
  const k=findAfter(rows,target);
  if(k>=rows.length||rows[k].t>target+maxTargetLagMs||rows[k].t>asOfMs){out.missingTarget++;continue;}
  out.evaluated++;
  p.push(Math.abs(rows[k].price-rows[i].price));
  m.push(Math.abs(rows[k].price-prediction));
 }
 out.issuanceCoverage=out.scheduled?out.eligible/out.scheduled:null;
 out.outcomeCoverage=out.matured?out.evaluated/out.matured:null;
 out.persistence=metrics(p);out.momentum30=metrics(m);
 out.pairedSkillVsPersistence=out.persistence.mae>0?1-out.momentum30.mae/out.persistence.mae:null;
 out.evidence='Retrospective historical observations only; no prospective or independent time witnessing';
 return out;
}

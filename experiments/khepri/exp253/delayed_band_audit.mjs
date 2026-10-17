/** Khepri 253 — delayed-outcome interval calibration; lab experiment only.
 * Forecasts issued at origin t for target t+h. An outcome can update the
 * calibrator only when t+h <= current origin. No claim of conformal coverage
 * under distribution shift or serial dependence.
 */
export const finiteQuantile=(values,coverage=.8)=>{
  if(!Number.isFinite(coverage)||coverage<=0||coverage>=1)throw Error('coverage must be in (0,1)');
  if(!Array.isArray(values)||!values.length||values.some(v=>!Number.isFinite(v)||v<0))throw Error('nonempty finite nonnegative errors required');
  const sorted=[...values].sort((a,b)=>a-b);
  return sorted[Math.min(sorted.length-1,Math.ceil((sorted.length+1)*coverage)-1)];
};
export class DelayedBand{
  constructor({h=7,window=120,coverage=.8,minLabels=30}={}){
    if(!Number.isInteger(h)||h<1||h>365||!Number.isInteger(window)||window<1||!Number.isInteger(minLabels)||minLabels<1||minLabels>window)throw Error('invalid horizon/window/minLabels');
    if(!Number.isFinite(coverage)||coverage<=0||coverage>=1)throw Error('invalid coverage');
    this.h=h;this.window=window;this.coverage=coverage;this.minLabels=minLabels;
    this.pending=new Map();this.errors=[];this.last=-1;this.matured=0;
  }
  observe(index,actual){
    if(index!==this.last+1)throw Error('observations must advance exactly one step');
    if(!Number.isFinite(actual)||actual<=0)throw Error('invalid actual');
    this.last=index;
    const matured=this.pending.get(index);
    if(matured){
      const error=Math.abs(actual/matured.point-1);
      this.errors.push(error);if(this.errors.length>this.window)this.errors.shift();
      this.pending.delete(index);this.matured++;
    }
  }
  issue(index,point){
    if(index!==this.last||this.pending.has(index+this.h))throw Error('observe current origin first; no duplicate target');
    if(!Number.isFinite(point)||point<=0)throw Error('invalid point');
    const band=this.errors.length>=this.minLabels?finiteQuantile(this.errors,this.coverage):null;
    this.pending.set(index+this.h,{origin:index,point});
    return {origin:index,target:index+this.h,band,labels:this.matured};
  }
}
const randStream=seed=>{
  let state=seed>>>0;
  const rand=()=>{state=(1664525*state+1013904223)>>>0;return (state+.5)/4294967296;};
  return ()=>Math.sqrt(-2*Math.log(rand()))*Math.cos(2*Math.PI*rand());
};
export function makePrices(scenario,seed=1,{n=1100,switchAt=700}={}){
  if(!Number.isInteger(n)||n<800||!Number.isInteger(switchAt)||switchAt<300||switchAt>=n-100)throw Error('invalid generator lengths');
  const normal=randStream(seed);let log=Math.log(2000),prev=0;const prices=[];
  for(let t=0;t<n;t++){
    let sigma=.005;
    if(scenario==='vol_up')sigma=t<switchAt?.003:.014;
    else if(scenario==='vol_down')sigma=t<switchAt?.014:.003;
    else if(scenario==='stable')sigma=.006;
    else if(scenario==='vol_pulse')sigma=t>=switchAt&&t<switchAt+70?.022:.005;
    else if(scenario==='autocorrelated')sigma=t<switchAt?.003:.012;
    else throw Error('unknown scenario');
    const r=(scenario==='autocorrelated'?.5*prev:0)+sigma*normal();
    log+=r;prev=r;prices.push(Math.exp(log));
  }
  return prices;
}
export function pointForecast(prices,t,h,method='persistence'){
  if(t<30||t>=prices.length||!Number.isInteger(h)||h<1)throw Error('invalid forecast origin/horizon');
  if(method==='persistence')return prices[t];
  if(method==='momentum'){
    let r=0;for(let j=t-19;j<=t;j++)r+=Math.log(prices[j]/prices[j-1]);
    return prices[t]*Math.exp(Math.max(-.012,Math.min(.012,r/20))*h*.45*Math.exp(-h/20));
  }
  throw Error('unknown forecast method');
}
const avg=a=>a.reduce((s,v)=>s+v,0)/a.length;
export function evaluateBands(prices,h,{evalStart=700,window=120,coverage=.8,method='persistence'}={}){
  if(!Array.isArray(prices)||prices.length<=evalStart+h+50||evalStart<350)throw Error('insufficient evaluation prices');
  const cal=new DelayedBand({h,window,coverage,minLabels:30});
  const records=[];let fixedBand=null;
  for(let t=0;t<prices.length;t++){
    cal.observe(t,prices[t]);
    if(t===evalStart)fixedBand=finiteQuantile(cal.errors,coverage);
    if(t<40||t+h>=prices.length)continue;
    const point=pointForecast(prices,t,h,method),issued=cal.issue(t,point);
    if(t>=evalStart)records.push({...issued,point,fixedBand,rollingBand:issued.band,actual:prices[t+h]});
  }
  const summary=key=>({
    coverage:avg(records.map(r=>Math.abs(r.actual/r.point-1)<=r[key]?1:0)),
    meanWidth:avg(records.map(r=>2*r.point*r[key]/r.actual)),
    first100Coverage:avg(records.slice(0,100).map(r=>Math.abs(r.actual/r.point-1)<=r[key]?1:0)),
    last100Coverage:avg(records.slice(-100).map(r=>Math.abs(r.actual/r.point-1)<=r[key]?1:0)),
  });
  return {n:records.length,h,method,fixed:summary('fixedBand'),rolling:summary('rollingBand'),
    initialBand:fixedBand,finalBand:records.at(-1).rollingBand,
    firstLabels:records[0].labels,records};
}
export function benchmark({seeds=30,n=1100,evalStart=700}={}){
  const rows=[];
  for(const scenario of ['vol_up','vol_down','stable','vol_pulse','autocorrelated'])for(const h of [7,30])for(const method of ['persistence','momentum']){
    const trials=[];
    for(let seed=1;seed<=seeds;seed++)trials.push(evaluateBands(makePrices(scenario,seed,{n,switchAt:evalStart}),h,{evalStart,method}));
    const m=(policy,metric)=>avg(trials.map(t=>t[policy][metric]));
    rows.push({scenario,h,method,seeds,staticCoverage:m('fixed','coverage'),rollingCoverage:m('rolling','coverage'),
      staticEarlyCoverage:m('fixed','first100Coverage'),rollingEarlyCoverage:m('rolling','first100Coverage'),
      staticLateCoverage:m('fixed','last100Coverage'),rollingLateCoverage:m('rolling','last100Coverage'),
      staticRelativeWidth:m('fixed','meanWidth'),rollingRelativeWidth:m('rolling','meanWidth')});
  }
  return {settings:{seeds,n,evalStart,coverageTarget:.8,window:120,synthetic:true},rows};
}
if(process.argv[1]&&import.meta.url===new URL('file://'+process.argv[1]).href){
  console.log(JSON.stringify(benchmark({seeds:Number(process.argv[2]??30)}),null,2));
}

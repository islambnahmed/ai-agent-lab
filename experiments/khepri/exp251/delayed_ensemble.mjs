/** Khepri 251: delayed-feedback expert ensemble. Research prototype only.
 * Three forecast experts are faithful formulas from gold-forecast/models.mjs
 * (persistence, momentum, mean_reversion). No network or market data used.
 * All weight updates require an actually matured target observation.
 */
const cap=(x,b)=>Math.max(-b,Math.min(b,x));
const mean=a=>a.reduce((s,v)=>s+v,0)/a.length;
export const EXPERTS=['persistence','momentum','mean_reversion'];
export function expertForecast(history,h,model){
  if(history.length<42||!Number.isInteger(h)||h<1||h>30||history.some(p=>!Number.isFinite(p)||p<=0))throw Error('invalid history/horizon');
  const last=history.at(-1);
  if(model==='persistence')return last;
  if(model==='momentum'){
    const t=history.slice(-21),r=mean(t.slice(1).map((p,i)=>Math.log(p/t[i])));
    return last*Math.exp(cap(r,0.012)*h*0.45*Math.exp(-h/20));
  }
  if(model==='mean_reversion'){
    const anchor=mean(history.slice(-40).map(Math.log));
    return Math.exp(Math.log(last)+(anchor-Math.log(last))*Math.min(0.6,h*0.025));
  }
  throw Error('unknown expert');
}
export function weightsFromScores(scores,temperature){
  if(!(temperature>0))throw Error('temperature must be positive');
  const logits=scores.map(s=>-s/temperature),m=Math.max(...logits);
  const e=logits.map(x=>Math.exp(x-m)),total=e.reduce((a,b)=>a+b,0);
  return e.map(x=>x/total);
}
export class DelayedEnsemble{
  constructor({h=7,decay=0.96,temperature=0.0025}={}){
    if(!Number.isInteger(h)||h<1||h>30||!(decay>=0&&decay<1)||!(temperature>0))throw Error('invalid parameters');
    this.h=h;this.decay=decay;this.temperature=temperature;this.scores=EXPERTS.map(()=>0);
    this.pending=new Map();this.lastIndex=-1;this.updates=0;this.updateLog=[];
  }
  step(index,history){
    if(index!==this.lastIndex+1||history.length!==index+1)throw Error('stream must advance one observation at a time');
    if(history.some(p=>!Number.isFinite(p)||p<=0))throw Error('invalid prices');
    this.lastIndex=index;
    const matured=this.pending.get(index);
    if(matured){
      const actual=history.at(-1);
      this.scores=this.scores.map((s,j)=>this.decay*s+(1-this.decay)*Math.abs(Math.log(matured.experts[j]/actual)));
      this.updates++;this.updateLog.push({at:index,origin:matured.origin});this.pending.delete(index);
    }
    if(index<41)return null;
    const experts=EXPERTS.map(m=>expertForecast(history,this.h,m));
    const weights=weightsFromScores(this.scores,this.temperature);
    const point=experts.reduce((s,p,j)=>s+p*weights[j],0);
    this.pending.set(index+this.h,{origin:index,experts});
    return {origin:index,target:index+this.h,experts,weights,point,updates:this.updates};
  }
}
export function makeSeries(scenario,seed=1,n=1250,switchAt=850){
  let state=seed>>>0;
  const rand=()=>{state=(1664525*state+1013904223)>>>0;return (state+0.5)/4294967296;};
  const normal=()=>Math.sqrt(-2*Math.log(rand()))*Math.cos(2*Math.PI*rand());
  let level=Math.log(2000),prev=0,anchor=level;
  const prices=[];
  for(let t=0;t<n;t++){
    const regime=scenario==='switch'?(t<switchAt?'trend':'mean_reversion'):scenario;
    if(scenario==='switch'&&t===switchAt)anchor=level;
    let r;
    if(regime==='random_walk')r=0.007*normal();
    else if(regime==='trend')r=0.0003+0.75*prev+0.004*normal();
    else if(regime==='mean_reversion')r=-0.18*(level-anchor)+0.007*normal();
    else throw Error('unknown scenario');
    level+=r;prev=r;prices.push(Math.exp(level));
  }
  return prices;
}
const absPct=(p,y)=>Math.abs(p/y-1);
export function evaluate(prices,h,{evalStart=850,decay=0.96,temperature=0.0025}={}){
  if(prices.length<evalStart+h+1)throw Error('not enough evaluation prices');
  const online=new DelayedEnsemble({h,decay,temperature});
  const forecasts=[];
  for(let t=0;t<prices.length;t++){
    const f=online.step(t,prices.slice(0,t+1));
    if(f)forecasts.push(f);
  }
  // Static model chosen ONLY on targets available before evaluation begins.
  const training=forecasts.filter(f=>f.origin>=100&&f.target<evalStart);
  const trainErrors=EXPERTS.map((_,j)=>mean(training.map(f=>absPct(f.experts[j],prices[f.target]))));
  const chosen=trainErrors.indexOf(Math.min(...trainErrors));
  const test=forecasts.filter(f=>f.origin>=evalStart&&f.target<prices.length);
  const expertMae=EXPERTS.map((_,j)=>mean(test.map(f=>absPct(f.experts[j],prices[f.target]))));
  const onlineMae=mean(test.map(f=>absPct(f.point,prices[f.target])));
  const equalMae=mean(test.map(f=>absPct(mean(f.experts),prices[f.target])));
  return {h,n:test.length,onlineMae,equalMae,staticMae:expertMae[chosen],persistenceMae:expertMae[0],oracleMae:Math.min(...expertMae),
    chosen:EXPERTS[chosen],expertMae,updates:online.updates,finalWeights:forecasts.at(-1).weights};
}
export function benchmark({seeds=40,n=1250,evalStart=850}={}){
  const rows=[];
  for(const scenario of ['random_walk','trend','mean_reversion','switch'])for(const h of [1,7,30]){
    const trials=[];
    for(let seed=1;seed<=seeds;seed++)trials.push(evaluate(makeSeries(scenario,seed,n,evalStart),h,{evalStart}));
    const avg=k=>mean(trials.map(t=>t[k]));
    rows.push({scenario,h,seeds,onlineMae:avg('onlineMae'),staticMae:avg('staticMae'),equalMae:avg('equalMae'),persistenceMae:avg('persistenceMae'),oracleMae:avg('oracleMae'),
      onlineBeatsStatic:trials.filter(t=>t.onlineMae<t.staticMae).length,
      onlineBeatsPersistence:trials.filter(t=>t.onlineMae<t.persistenceMae).length,
      counterexampleSeed:trials.findIndex(t=>t.onlineMae>t.staticMae)+1});
  }
  return {settings:{seeds,n,evalStart,decay:0.96,temperature:0.0025,seeded:true,prices:'synthetic, not gold market'},rows};
}
if(process.argv[1]&&import.meta.url===new URL('file://'+process.argv[1]).href){
  const report=benchmark({seeds:Number(process.argv[2]??40)});
  console.log(JSON.stringify(report,null,2));
}

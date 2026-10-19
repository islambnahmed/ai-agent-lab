/**
 * Synthetic regime challenge for the ACTUAL Gold Lab v2 predict() implementation.
 * No real gold data, no trading claims, no model promotion. Node >=22.
 * Run: node tools/gold_production_regime_probe.mjs > stress-results.json
 */
import {predict, MODEL_NAMES, MODEL_VERSION} from '../products/gold-forecast/models.mjs';

const mean = xs => xs.reduce((a,b)=>a+b,0)/xs.length;
const mae = rows => mean(rows.map(r=>Math.abs(r.point-r.actual)));
const seedRandom = seed => {let state=seed>>>0;return ()=>{state=(Math.imul(1664525,state)+1013904223)>>>0;return (state+0.5)/4294967296;};};
function gaussian(rand){return Math.sqrt(-2*Math.log(rand()))*Math.cos(2*Math.PI*rand());}
export function generate(name,{n=420,seed=1729}={}){
  if(!Number.isInteger(n)||n<330)throw Error('n must be >=330');
  const rand=seedRandom(seed),prices=[2500];
  for(let i=1;i<n;i++){
    let drift=0,noise=0;
    switch(name){
      case 'steady_up':drift=0.001;break;
      case 'up_to_down':drift=i<Math.floor(n*.62)?0.0015:-0.0018;break;
      case 'down_to_up':drift=i<Math.floor(n*.62)?-0.0015:0.0018;break;
      case 'mean_reverting':drift=-.12*Math.log(prices.at(-1)/2500);noise=.006*gaussian(rand);break;
      case 'random_walk':noise=.008*gaussian(rand);break;
      case 'shock_recovery':drift=.0006;noise=i===Math.floor(n*.81)?-.18:(i>Math.floor(n*.81)&&i<Math.floor(n*.9)?0.002:0);break;
      default:throw Error('Unknown scenario '+name);
    }
    prices.push(prices.at(-1)*Math.exp(drift+noise));
  }
  return prices;
}
export const SCENARIOS=['steady_up','up_to_down','down_to_up','mean_reverting','random_walk','shock_recovery'];
export function evaluate(prices,h,{selectionStart=65}={}){
  if(![1,7,30].includes(h)||prices.length<330||prices.some(x=>!Number.isFinite(x)||x<=0))throw Error('Invalid evaluation input');
  const n=prices.length,selectionEnd=Math.floor(.6*n),auditStart=Math.floor(.8*n),models=Object.keys(MODEL_NAMES);
  const scores=[];
  for(const model of models){
    const selection=[];
    for(let i=selectionStart;i<=selectionEnd-h;i++){
      selection.push({point:predict(prices.slice(0,i),h,model),actual:prices[i+h-1]});
    }
    scores.push({model,mae:mae(selection),n:selection.length});
  }
  scores.sort((a,b)=>a.mae-b.mae);
  const selected=scores[0].model,rows=[];
  for(let i=auditStart;i<=n-h;i++){
    const origin=prices[i-1],actual=prices[i+h-1];
    rows.push({originIndex:i-1,point:predict(prices.slice(0,i),h,selected),baseline:origin,actual});
  }
  const baseline=mae(rows.map(r=>({point:r.baseline,actual:r.actual})));
  const candidate=mae(rows);
  const phases=[];
  for(let offset=0;offset<h;offset++){
    const group=rows.filter((_,j)=>j%h===offset);
    if(!group.length)continue;
    const b=mae(group.map(r=>({point:r.baseline,actual:r.actual}))),c=mae(group);
    phases.push({offset,n:group.length,skillPct:b>0?100*(1-c/b):null});
  }
  const skillPct=baseline>0?100*(1-candidate/baseline):null;
  return {h,selected,selection:scores,audit:{n:rows.length,baselineMae:baseline,modelMae:candidate,skillPct},
    phaseRange:{min:Math.min(...phases.map(p=>p.skillPct)),max:Math.max(...phases.map(p=>p.skillPct)),nMin:Math.min(...phases.map(p=>p.n))},
    phase0:phases[0],split:{selectionEnd,auditStart,purgedOriginsPerBoundary:h-1}};
}
export function run({n=420,seed=1729,scenarios=SCENARIOS,horizons=[1,7,30]}={}){
  return {experiment:'synthetic-production-model-regime-probe',modelVersion:MODEL_VERSION,seed,n,
    data:'SYNTHETIC — not real gold prices',selectedOn:'oldest 60%; no audit selection; 20% calibration gap',
    cases:scenarios.flatMap(scenario=>{const prices=generate(scenario,{n,seed});return horizons.map(h=>({scenario,...evaluate(prices,h)}));}),
    caveats:['Retrospective synthetic counterexamples, not estimates of live XAU/USD skill.',
      'All horizon targets are observed-index steps; overlapping errors are dependent.',
      'Phase ranges are descriptive; short 30-close phase groups cannot establish significance.',
      'Gold Lab production forecast() also validates sources and calibrates intervals; this probe isolates its exact predict() models and selection MAE.']};
}
if(import.meta.url===new URL('file://'+process.argv[1]).href)console.log(JSON.stringify(run(),null,2));

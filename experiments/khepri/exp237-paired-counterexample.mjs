// Khepri 237: marginal MAE/RMSE do not identify paired uncertainty.
// Constructed errors, NOT actual forecasts. Node >=18, no dependencies.
import assert from 'node:assert/strict';
const n=613;
const make=(mae,rmse)=>{
  const k=Math.floor(n/2),v=rmse*rmse-mae*mae;
  const lo=mae-Math.sqrt(v*(n-k)/k),hi=mae+Math.sqrt(v*k/(n-k));
  assert(lo>=0);
  return [...Array(k).fill(lo),...Array(n-k).fill(hi)];
};
const mean=xs=>xs.reduce((s,x)=>s+x,0)/xs.length;
const summarize=(a,b)=>{
  const d=a.map((x,i)=>b[i]-x),delta=mean(d);
  const sd=Math.sqrt(d.reduce((s,x)=>s+(x-delta)**2,0)/(n-1));
  return {delta,pairedSeIidOnly:sd/Math.sqrt(n),
    illustrativeIid95:[delta-1.96*sd/Math.sqrt(n),delta+1.96*sd/Math.sqrt(n)]};
};
const a=make(158.46169262380107,209.91182037106645);
const b=make(168.72494850792106,232.54294324624234);
const moment=x=>({mae:mean(x),rmse:Math.sqrt(mean(x.map(y=>y*y)))});
const aligned=summarize(a,b),reversed=summarize(a,[...b].reverse());
assert(Math.abs(aligned.delta-reversed.delta)<1e-9);
assert(reversed.pairedSeIidOnly>10*aligned.pairedSeIidOnly);
assert(Math.abs(moment(a).mae-158.46169262380107)<1e-9);
assert(Math.abs(moment(b).rmse-232.54294324624234)<1e-9);
console.log(JSON.stringify({source:'research-benchmark-20261012.json ablation h30 audit',n,
  price:moment(a),macro:moment(b),aligned,reversed,
  warning:'Constructed counterexample, not actual forecast pairs; iid intervals illustrative only'},null,2));

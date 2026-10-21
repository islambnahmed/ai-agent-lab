/** Research-only deterministic stress test of the current gold forecast model.
 * Usage from products/gold-forecast: node scripts/khepri-exp355-stress.mjs
 * No network, secrets, provider data, trades, or production writes.
 */
import assert from 'node:assert/strict';
import {forecast} from '../forecast.mjs';
const N=360,ASOF='2026-01-01T00:00:00Z';
const mean=xs=>xs.reduce((s,x)=>s+x,0)/xs.length;
function generator(seed){let x=seed>>>0;return ()=>{x=(Math.imul(1664525,x)+1013904223)>>>0;return (x+.5)/4294967296;};}
function normal(rand){return Math.sqrt(-2*Math.log(rand()))*Math.cos(2*Math.PI*rand());}
function series(kind,seed){
  const rand=generator(seed),out=[];let price=Math.log(2500);
  for(let i=0;i<N;i++){
    const shifted=i>=288;
    const sigma=kind==='volatility_shift'&&shifted?.024:.0025;
    const drift=kind==='trend_reversal'?(shifted?-.0025:.0015):.0005;
    price+=drift+sigma*normal(rand);
    if(kind==='level_jump'&&i===288)price+=.12;
    out.push({date:new Date(Date.UTC(2024,0,1+i)).toISOString().slice(0,10),price:Math.exp(price)});
  }
  return out;
}
function testOne(kind,seed,h){
  const rows=series(kind,seed),r=forecast(rows,h,{asOf:ASOF,includeRows:true});
  const returns=rows.map((v,i)=>i?Math.log(v.price/rows[i-1].price):0);
  const sd=xs=>{const avg=mean(xs);return Math.sqrt(mean(xs.map(x=>(x-avg)**2)));};
  const ratios=r.rows.audit.map(v=>sd(returns.slice(v.originIndex-19,v.originIndex+1))/Math.max(1e-12,sd(returns.slice(v.originIndex-99,v.originIndex-19))));
  const factors=ratios.map(v=>Math.max(1,Math.min(6,v)));
  const adapted=100*mean(r.rows.audit.map((v,i)=>v.bandError<=r.band*factors[i]?1:0));
  const kept=r.rows.audit.filter((_,i)=>ratios[i]<=3);
  return {kind,seed,h,model:r.model,calibration:100*mean(r.rows.calibration.map(v=>v.bandError<=r.band?1:0)),
    audit:r.coverage,adaptive:adapted,bandInflation:mean(factors),
    retained:kept.length/r.rows.audit.length,keptCoverage:kept.length?100*mean(kept.map(v=>v.bandError<=r.band?1:0)):null};
}
const kinds=['stable','volatility_shift','trend_reversal','level_jump'];
const output=[];
for(const kind of kinds)for(const h of [1,7,30]){
  const runs=Array.from({length:12},(_,i)=>testOne(kind,i+1,h));
  output.push({kind,h,n:runs.length,calibration:mean(runs.map(r=>r.calibration)),
    audit:mean(runs.map(r=>r.audit)),adaptive:mean(runs.map(r=>r.adaptive)),
    bandInflation:mean(runs.map(r=>r.bandInflation)),retained:mean(runs.map(r=>r.retained)),
    keptCoverage:mean(runs.map(r=>r.keptCoverage??0))});
}
const get=(kind,h)=>output.find(x=>x.kind===kind&&x.h===h);
assert.ok(get('stable',7).audit>70);
assert.ok(get('volatility_shift',7).audit<25);
assert.ok(get('volatility_shift',7).adaptive<50);
assert.ok(get('trend_reversal',30).audit<20);
assert.ok(get('volatility_shift',7).calibration===get('stable',7).calibration);
assert.ok(get('volatility_shift',7).retained<.8);
console.log(JSON.stringify({experiment:'khepri-exp355',synthetic:true,seedRange:[1,12],groups:output},null,2));

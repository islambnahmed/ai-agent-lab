// Seshat c295: run with node products/gold-forecast/experiments/seshat-c295/direct-forecast-audit.mjs
// Synthetic research only. Does not change production forecast or use market data.
import assert from 'node:assert/strict';
import {forecast} from '../../forecast.mjs';
const horizons=[1,7,30], N=60, prefixLength=360, maxH=30;
function rng(seed){let x=seed>>>0;return()=>{x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)/4294967296;};}
function normal(r){return Math.sqrt(-2*Math.log(Math.max(1e-12,r())))*Math.cos(2*Math.PI*r());}
function generate(seed){
  const r=rng(seed*97+12519),z=Array.from({length:prefixLength+maxH},()=>normal(r));
  let p=2400;const history=[];
  for(let i=0;i<prefixLength;i++){
    if(i)p*=Math.exp(0.00015+0.004*z[i]);
    history.push({date:new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10),price:p});
  }
  const future={};
  for(const [name,scale] of [['stable',1],['shock',8]]){
    let q=p;future[name]=[];
    for(let j=0;j<maxH;j++){q*=Math.exp(0.00015+0.004*scale*z[prefixLength+j]);future[name].push(q);}
  }
  return {history,future};
}
for(const start of [1,1001]){
  const totals=Object.fromEntries(horizons.map(h=>[h,{n:0,audit:0,stable:0,shock:0}]));
  for(let seed=start;seed<start+N;seed++){
    const {history,future}=generate(seed);
    const asOf=new Date(Date.parse(history.at(-1).date+'T00:00:00Z')+86400000).toISOString().slice(0,10)+'T12:00:00Z';
    for(const h of horizons){
      const f=forecast(history,h,{asOf}),t=totals[h];
      assert.equal(f.dataQuality.rows,prefixLength);
      assert.ok(f.lower<=f.point&&f.point<=f.upper);
      t.n++;t.audit+=f.coverage;
      for(const scenario of ['stable','shock']){
        const actual=future[scenario][h-1];
        t[scenario]+=Number(actual>=f.lower&&actual<=f.upper);
      }
      if(seed===start){
        const same=forecast([...history,{date:asOf.slice(0,10),price:1e7}],h,{asOf});
        assert.equal(same.point,f.point);assert.equal(same.lower,f.lower);
        assert.equal(same.upper,f.upper);assert.equal(same.coverage,f.coverage);
        assert.equal(same.dataQuality.excludedSameDay,1);
        const nextDay=new Date(Date.parse(asOf.slice(0,10)+'T00:00:00Z')+86400000).toISOString().slice(0,10);
        assert.throws(()=>forecast([...history,{date:nextDay,price:1e7}],h,{asOf}),/Future-dated/);
      }
    }
  }
  const summary=Object.fromEntries(horizons.map(h=>{const t=totals[h];return[h,{n:t.n,retrospectivePct:100*t.audit/(t.n*100),stablePct:100*t.stable/t.n,shockPct:100*t.shock/t.n}]}));
  console.log(JSON.stringify({startSeed:start,summary},null,2));
  assert.ok(summary[1].shockPct<35&&summary[7].shockPct<35&&summary[30].shockPct<35,'8x shock should defeat unadapted intervals');
}

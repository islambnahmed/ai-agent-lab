import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {forecastCalibrated} from '../forecast_calibrated.mjs';
import {forecast,predict} from '../forecast.mjs';

function synthetic(kind,n=420){
  let p=2500;
  return Array.from({length:n},(_,i)=>{
    const drift=kind==='up'?0.0015:kind==='down'?-0.0015:i<n*.8?0.001:-0.008;
    p*=Math.exp(drift+0.004*Math.sin(i*1.17)+0.001*Math.cos(i*.39));
    return {date:new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10),price:p};
  });
}

test('coverage equals held-out hits in displayed bounds in nine scenarios',()=>{
  for(const kind of ['up','down','shift'])for(const h of [1,7,30]){
    const raw=synthetic(kind),fixed=forecastCalibrated(raw,h),old=forecast(raw,h);
    const prices=raw.map(x=>x.price),split=Math.floor(prices.length*.8);
    const radius=Math.log1p(fixed.band);
    let hits=0,total=0;
    for(let i=split;i<prices.length-h+1;i++){
      const point=predict(prices.slice(0,i),h,fixed.model),actual=prices[i+h-1];
      const lower=point*Math.exp(-radius),upper=point*Math.exp(radius);
      hits+=(actual>=lower-1e-8 && actual<=upper+1e-8)?1:0;
      total++;
    }
    assert.ok(Math.abs(fixed.coverage-100*hits/total)<1e-9,`${kind} h${h}`);
    assert.equal(fixed.point,old.point);
    assert.equal(fixed.audit.mae,old.audit.mae);
  }
});

test('counterexample: MAPE hit is not necessarily a displayed interval hit',()=>{
  const predicted=90,actual=100,band=Math.abs(predicted-actual)/actual;
  assert.equal(band,.1);
  assert.equal(actual<=predicted*(1+band),false);
});

test('dashboard uses calibrated evaluator in render and CSV preflight',()=>{
  const app=readFileSync(new URL('../app.mjs',import.meta.url),'utf8');
  assert.match(app,/import\s*\{forecastCalibrated\}\s*from\s*["']\.\/forecast_calibrated\.mjs["']/);
  assert.equal((app.match(/\bforecastCalibrated\(/g)||[]).length,2);
  assert.equal((app.match(/\bforecast\(/g)||[]).length,0);
});

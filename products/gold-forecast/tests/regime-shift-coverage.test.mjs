// Adversarial, deterministic counterexample: historical calibration coverage is
// not a guarantee after a volatility/regime shift. No real gold data is used.
// This regression intentionally preserves the system's honest caveat rather
// than "fixing" coverage by looking at the audit period.
import test from 'node:test';
import assert from 'node:assert/strict';
import {forecast} from '../forecast.mjs';

const AS_OF = '2026-10-21T00:00:00Z';
const N = 400;
const AUDIT_START = Math.floor(N * 0.8);

function series({shock=false}={}){
  return Array.from({length:N},(_,i)=>({
    date:new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10),
    price:shock && i>=AUDIT_START
      ? (i%2===0?2700:2300)
      : 2500+3*Math.sin(i*0.17)
  }));
}

test('stable low-noise control achieves high empirical holdout coverage',()=>{
  const result=forecast(series(),1,{asOf:AS_OF});
  assert.equal(result.split.auditStart,AUDIT_START);
  assert.ok(result.coverage>=95, 'control should be inside the calibrated band');
  assert.ok(result.audit.n>=50);
});

test('sudden volatility shift defeats a historically calibrated interval',()=>{
  for(const horizon of [1,7]){
    const result=forecast(series({shock:true}),horizon,{asOf:AS_OF});
    assert.equal(result.split.auditStart,AUDIT_START);
    assert.ok(result.calibration.n>=10);
    assert.ok(result.band<0.02,'pre-shift calibration is deliberately narrow');
    assert.ok(result.coverage<25,
      'a 80%-rank historical band can have very low post-shift coverage; h='+horizon);
    assert.equal(result.evidence,
      'Retrospective reconstruction from current data vintage; prospective skill is unproven');
  }
});

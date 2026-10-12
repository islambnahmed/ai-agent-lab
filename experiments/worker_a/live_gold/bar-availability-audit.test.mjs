import test from 'node:test';
import assert from 'node:assert/strict';
import {closeAvailableAt,auditCandleForecast} from './bar-availability-audit.mjs';
const t=Date.parse('2025-01-08T12:00:00Z'), m=60_000;
const f=(args={})=>auditCandleForecast({originStampMs:t,targetStampMs:t+75*m,issuedAtMs:t,...args});
test('open-stamped 12:00 close unavailable until 12:05: reject false 12:00 issue',()=>{
  const a=f({stampConvention:'open'});
  assert.equal(a.status,'lookahead_origin_not_yet_available');
  assert.equal(a.originAvailableAtMs,t+5*m);
  assert.equal(a.eligibleFor75mClaim,false);
});
test('open-stamped issue at 12:05 has exactly 75m lead',()=>{
  const a=f({stampConvention:'open',issuedAtMs:t+5*m});
  assert.equal(a.status,'timing_eligible');
  assert.equal(a.effectiveLeadMs,75*m);
});
test('close-stamped issue at 12:00 has exactly 75m lead',()=>{
  const a=f({stampConvention:'close'});
  assert.equal(a.status,'timing_eligible');
});
test('later issuance changes effective horizon, cannot advertise 75m',()=>{
  const a=f({stampConvention:'open',issuedAtMs:t+7*m});
  assert.equal(a.status,'effective_horizon_not_75m');
  assert.equal(a.effectiveLeadMs,73*m);
});
test('known publication delay must be respected',()=>{
  assert.equal(f({stampConvention:'close',publishDelayMs:90_000}).status,'lookahead_origin_not_yet_available');
  assert.equal(f({stampConvention:'close',publishDelayMs:90_000,issuedAtMs:t+90_000}).status,'timing_eligible');
});
test('outcome known before issuance rejected',()=>{
  assert.equal(f({stampConvention:'close',issuedAtMs:t+76*m}).status,'outcome_already_available');
});
test('no default timestamp convention allowed',()=>assert.throws(()=>f(),/stampConvention/));
test('reject wrong candle horizon',()=>assert.throws(()=>f({stampConvention:'close',targetStampMs:t+70*m}),/exactly 75/));
test('reject invalid publication delay',()=>assert.throws(()=>f({stampConvention:'close',publishDelayMs:-1}),/publishDelay/));
test('reject non-grid timestamp',()=>assert.throws(()=>closeAvailableAt(t+1,{stampConvention:'close'}),/5-minute/));
test('reject fractional issuance timestamp',()=>assert.throws(()=>f({stampConvention:'close',issuedAtMs:t+.5}),/issuance/));

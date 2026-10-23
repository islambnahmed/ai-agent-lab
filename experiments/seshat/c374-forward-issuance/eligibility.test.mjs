import test from 'node:test';
import assert from 'node:assert/strict';
import {prospectiveEligibility as gate} from './eligibility.mjs';
const issuedAt='2026-10-24T00:10:30Z';
test('stale H1 blocked when next close may predate issue',()=>{
  const r=gate({originDate:'2026-10-22',issuedAt,horizon:1});
  assert.equal(r.eligible,false);assert.equal(r.earliestTargetDate,'2026-10-23');
});
test('H7 future despite two-day provider lag',()=>{
  const r=gate({originDate:'2026-10-22',issuedAt,horizon:7});
  assert.equal(r.eligible,true);assert.equal(r.earliestTargetDate,'2026-10-29');
});
test('H30 future despite unknown holidays',()=>{
  const r=gate({originDate:'2026-10-22',issuedAt,horizon:30});
  assert.equal(r.eligible,true);assert.equal(r.earliestTargetDate,'2026-11-21');
});
test('same UTC target day blocked',()=>{
  assert.equal(gate({originDate:'2026-10-23',issuedAt:'2026-10-24T23:59:59Z',horizon:1}).eligible,false);
});
test('H1 eligible when origin and issue same day',()=>{
  assert.equal(gate({originDate:'2026-10-23',issuedAt:'2026-10-23T23:59:59Z',horizon:1}).eligible,true);
});
test('leap and year boundaries',()=>{
  assert.equal(gate({originDate:'2024-02-28',issuedAt:'2024-02-28T12:00:00Z',horizon:1}).earliestTargetDate,'2024-02-29');
  assert.equal(gate({originDate:'2026-12-31',issuedAt:'2026-12-31T12:00:00Z',horizon:1}).earliestTargetDate,'2027-01-01');
});
test('reject future origin and invalid date',()=>{
  assert.throws(()=>gate({originDate:'2026-10-25',issuedAt,horizon:7}),/future/);
  assert.throws(()=>gate({originDate:'2026-02-30',issuedAt,horizon:7}),/invalid date/);
});
test('reject timezone ambiguity and invalid horizons',()=>{
  assert.throws(()=>gate({originDate:'2026-10-22',issuedAt:'2026-10-24T00:10:30+03:00',horizon:7}),/UTC/);
  assert.throws(()=>gate({originDate:'2026-10-22',issuedAt,horizon:0}),/horizon/);
  assert.throws(()=>gate({originDate:'2026-10-22',issuedAt,horizon:1.5}),/horizon/);
});

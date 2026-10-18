import test from 'node:test';
import assert from 'node:assert/strict';
import {validateReceiptSemantics as gate} from '../receipt-semantics.mjs';
const valid=()=>({
  schemaVersion:1,codeCommit:'a'.repeat(40),historyHash:'b'.repeat(64),
  source:'Example feed',modelVersion:'gold-v2.0.0',model:'persistence',
  sourceManifest:{receivedAt:'2026-10-16T10:00:00Z'},issuedAt:'2026-10-16T10:05:00Z',
  horizon:7,historyLength:260,originDate:'2026-10-15',originClose:4300,baseline:4300,
  point:4320,lower:4200,upper:4400,calendar:'weekdays',targetDate:'2026-10-26'
});
const changed=(path,value)=>{const r=valid();if(path.includes('.')){const [a,b]=path.split('.');r[a][b]=value;}else r[path]=value;return r;};
const rejected=(path,value,reason)=>assert.throws(()=>gate(changed(path,value)),reason);
test('valid daily, weekday, and irregular-cadence receipts pass',()=>{
  assert.equal(gate(valid()),true);
  assert.equal(gate({...valid(),calendar:'daily',targetDate:'2026-10-22'}),true);
  assert.equal(gate({...valid(),calendar:'observations',targetDate:null}),true);
});
test('reject malformed, missing, and future source snapshots',()=>{
  rejected('sourceManifest',null,/manifest/i);
  rejected('sourceManifest.receivedAt','2026-10-16T10:06:00Z',/snapshot/i);
  rejected('sourceManifest.receivedAt','2026-10-16T09:00:00Z',/snapshot/i);
  rejected('issuedAt','2026-10-16T10:05:00',/timezone/i);
});
test('reject fabricated target date and unknown calendar',()=>{
  rejected('targetDate','2026-10-23',/Target date inconsistent/i);
  rejected('targetDate','2026-02-30',/nonexistent/i);
  rejected('calendar','AM',/calendar/i);
  assert.throws(()=>gate({...valid(),calendar:'observations',targetDate:'2026-10-26'}),/must not invent/i);
});
test('reject invalid numeric forecasts, inverted intervals, or wrong baseline',()=>{
  rejected('point',NaN,/Forecast point/i);
  rejected('point',Infinity,/Forecast point/i);
  rejected('lower',-1,/Lower bound/i);
  rejected('upper',0,/Upper bound/i);
  rejected('lower',4330,/outside interval/i);
  rejected('baseline',4301,/baseline must equal/i);
});
test('reject invalid hashes and inconsistent horizons',()=>{
  rejected('codeCommit','not-a-commit',/commit SHA/i);
  rejected('historyHash','0'.repeat(40),/SHA-256/i);
  rejected('horizon',5,/horizon/i);
  rejected('historyLength',100,/history/i);
  assert.throws(()=>gate({...valid(),horizon:30,historyLength:165}),/history/i);
  rejected('originDate','2026-10-16',/predate/i);
  rejected('originDate','2026-02-30',/nonexistent/i);
});
test('reject empty identification and unsupported schema',()=>{
  rejected('source',' ',/Source required/i);
  rejected('model','',/Model identification/i);
  rejected('schemaVersion',2,/schema/i);
});

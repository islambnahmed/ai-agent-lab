import test from 'node:test';
import assert from 'node:assert/strict';
import {buildSnapshot,FROZEN} from './evidence_snapshot.mjs';
import {makeView} from './dashboard_view.mjs';
const row=(date,price)=>({date,price,capturedAt:'2026-10-30T11:00:00Z',sourceId:FROZEN.sourceId,sourceSession:FROZEN.sourceSession});
test('omitting early provider rows cannot silently reassign horizon-1 score',()=>{
  const all=[row('2026-10-19',4100),row('2026-10-20',4200),row('2026-10-21',4300)];
  for(const observations of [all,[all[2]]]){
    const snapshot=buildSnapshot({asOf:'2026-10-30T12:00:00Z',observations});
    const f=makeView(snapshot,'en').forecasts[0];
    assert.equal(f.status,'sequence_unverified');
    assert.equal(f.score,null);
    assert.equal(snapshot.forecasts[0].targetDate,undefined);
    assert.equal(snapshot.forecasts[0].improvementUsd,undefined);
  }
});
test('seven caller-provided observations cannot establish a verified seventh fixing',()=>{
  const observations=Array.from({length:7},(_,i)=>row('2026-10-'+String(i+19).padStart(2,'0'),4180+i));
  const s=buildSnapshot({asOf:'2026-10-30T12:00:00Z',observations});
  assert.equal(s.forecasts[1].status,'sequence_unverified');
  assert.equal(s.forecasts[1].challengerAbsoluteError,undefined);
});

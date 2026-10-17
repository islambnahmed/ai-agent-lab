import test from 'node:test';
import assert from 'node:assert/strict';
import {buildSnapshot,FROZEN} from './evidence_snapshot.mjs';
import {makeView} from './dashboard_view.mjs';
const base={asOf:'2026-10-30T12:00:00Z'};
const row=(date,price)=>({date,price,capturedAt:'2026-10-30T11:00:00Z',sourceId:FROZEN.sourceId,sourceSession:FROZEN.sourceSession});
const pending=buildSnapshot(base);
test('three frozen predictions render with exact cents',()=>assert.deepEqual(makeView(pending).forecasts.map(f=>f.price),['4176.90','4168.68','4154.57']));
test('pending never emits a score',()=>assert.ok(makeView(pending).forecasts.every(f=>f.score===null)));
test('Arabic and English translations preserve all forecast values',()=>{const a=makeView(pending,'ar'),b=makeView(pending,'en');assert.equal(a.dir,'rtl');assert.equal(b.dir,'ltr');assert.deepEqual(a.forecasts.map(f=>f.price),b.forecasts.map(f=>f.price))});
test('unverified provider sequence cannot emit a score',()=>{const v=makeView(buildSnapshot({...base,observations:[row('2026-10-19',4180)]}),'en');assert.equal(v.forecasts[0].status,'sequence_unverified');assert.match(v.forecasts[0].description,/sequence unverified/);assert.equal(v.forecasts[0].score,null)});
test('rejects fabricated verified status',()=>{const s=structuredClone(pending);s.forecasts[0].status='verified';assert.throws(()=>makeView(s),/Unrecognized/)});
test('rejects extra forecast or missing horizon',()=>{const s=structuredClone(pending);s.forecasts.push(s.forecasts[0]);assert.throws(()=>makeView(s),/Invalid/);s.forecasts.pop();s.forecasts[0].horizon=30;assert.throws(()=>makeView(s),/Unrecognized/)});
test('rejects malformed numeric values and unsupported language',()=>{const s=structuredClone(pending);s.forecasts[0].point=Infinity;assert.throws(()=>makeView(s),/Unrecognized/);assert.throws(()=>makeView(pending,'fr'),/language/)});
test('anchors to the published commit, not an invented timestamp',()=>assert.match(makeView(pending).anchorUrl,/609fc40a6233ea25ff1f6716a5bcc5df8c37f321$/));
test('index imports evidence gate and avoids external requests',async()=>{const fs=await import('node:fs/promises');const html=await fs.readFile(new URL('./index.html',import.meta.url),'utf8');const app=await fs.readFile(new URL('./dashboard_app.mjs',import.meta.url),'utf8');assert.match(app,/import \{buildSnapshot\}/);assert.match(app,/observations:\[\]/);assert.doesNotMatch(app,/fetch\(/);assert.match(html,/script-src 'self'/);assert.match(html,/src="\.\/dashboard_app\.mjs"/)});
test('rejects a forged but well-formed anchor SHA',()=>{const s=structuredClone(pending);s.anchorCommit='a'.repeat(40);assert.throws(()=>makeView(s),/Invalid/)});
test('rejects forged batch, reference, or source metadata',()=>{for(const [key,value] of [['batchId','other'],['reference',{...pending.reference,price:4200}],['reference',{...pending.reference,sourceId:'other'}]]){const s=structuredClone(pending);s[key]=value;assert.throws(()=>makeView(s),/Invalid/);}});
test('rejects plausible numeric forecast tampering',()=>{const s=structuredClone(pending);s.forecasts[0].point+=1;assert.throws(()=>makeView(s),/Unrecognized/)});
test('rejects invented matured scores even when numbers look plausible',()=>{const s=buildSnapshot({...base,observations:[row('2026-10-19',4180)]});s.forecasts[0].challengerAbsoluteError=0;assert.throws(()=>makeView(s),/Inconsistent unscored/);});
test('rejects fake pending or matured transitions and counts',()=>{const s=structuredClone(pending);s.forecasts[0].status='matured_timing_unverified';s.forecasts[0].baselineAbsoluteError=1;s.forecasts[0].challengerAbsoluteError=1;assert.throws(()=>makeView(s),/Unrecognized/);const t=structuredClone(pending);t.observedSinceOrigin=7;assert.throws(()=>makeView(t),/Inconsistent unscored/);});
test('rejects pending forecasts carrying hidden scores',()=>{const s=structuredClone(pending);s.forecasts[0].challengerAbsoluteError=0;assert.throws(()=>makeView(s),/Inconsistent unscored/);});

test('legacy scored snapshots cannot be upgraded into the new schema',()=>{
  const s=buildSnapshot({...base,observations:[row('2026-10-19',4180)]});
  s.schemaVersion=1;assert.throws(()=>makeView(s),/Invalid/);
  s.schemaVersion=2;s.forecasts[0].status='matured_timing_unverified';
  assert.throws(()=>makeView(s),/Unrecognized/);
});
test('rejects hidden target metadata in sequence-unverified state',()=>{
  const s=buildSnapshot({...base,observations:[row('2026-10-19',4180)]});
  for(const [key,value] of [['targetDate','2026-10-19'],['improvementUsd',5],['directionCorrect',true]]){
    const c=structuredClone(s);c.forecasts[0][key]=value;
    assert.throws(()=>makeView(c),/Inconsistent unscored/);
  }
});

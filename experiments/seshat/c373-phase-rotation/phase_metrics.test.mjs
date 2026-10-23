import test from 'node:test';
import assert from 'node:assert/strict';
import {auditPhases} from './phase_metrics.mjs';
const rows=(actuals,points)=>actuals.map((actual,i)=>({originIndex:i,targetDate:`2026-10-${String(i+1).padStart(2,'0')}`,actual,point:points[i]}));
test('persistence model ties baseline in every phase',()=>{
 const b=rows([100,101,99,105,104,102],[100,100,100,100,100,100]);
 const a=auditPhases(b,b,3);
 assert.equal(a.pooledSkillPct,0);assert.equal(a.phaseSummary.zero,3);
 assert.deepEqual(a.phases.map(p=>p.n),[2,2,2]);
});
test('single offset can win while pooled skill loses',()=>{
 const b=rows([100,100,100,100,100,100],[110,110,110,110,110,110]);
 const m=rows([100,100,100,100,100,100],[100,130,130,100,130,130]);
 const a=auditPhases(m,b,3);
 assert.equal(a.phases[0].skillPct,100);
 assert.equal(a.phaseSummary.label,'mixed_sign');
 assert.ok(a.pooledSkillPct<0);
 assert.equal(a.phaseSummary.positive,1);assert.equal(a.phaseSummary.negative,2);
});
test('all offsets represented and no data silently discarded',()=>{
 const b=rows([100,100,100,100,100],[110,110,110,110,110]);
 const m=rows([100,100,100,100,100],[109,109,109,109,109]);
 const a=auditPhases(m,b,3);
 assert.deepEqual(a.phases.map(p=>p.n),[2,2,1]);
 assert.ok(Math.abs(a.pooledSkillPct-10)<1e-12);
 assert.equal(a.phases.reduce((s,p)=>s+p.n,0),5);
});
test('rejects non-paired target dates, prices, and origins',()=>{
 const b=rows([100],[110]);
 assert.throws(()=>auditPhases(rows([101],[110]),b,1),/unpaired/);
 assert.throws(()=>auditPhases([{...b[0],targetDate:'2026-11-01'}],b,1),/unpaired/);
 assert.throws(()=>auditPhases([{...b[0],originIndex:7}],b,1),/unpaired/);
});
test('rejects invalid inputs',()=>{
 const b=rows([100],[110]);
 assert.throws(()=>auditPhases(b,b,0));
 assert.throws(()=>auditPhases([],[],1));
 assert.throws(()=>auditPhases(b,[],1));
 assert.throws(()=>auditPhases([{...b[0],actual:NaN}],b,1));
});
test('handles zero baseline error without claiming finite skill',()=>{
 const b=rows([100],[100]);const m=rows([100],[101]);
 const a=auditPhases(m,b,1);
 assert.equal(a.pooledSkillPct,null);assert.equal(a.phases[0].skillPct,null);
});

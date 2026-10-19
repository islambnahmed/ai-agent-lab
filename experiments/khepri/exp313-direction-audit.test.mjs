import test from 'node:test';
import assert from 'node:assert/strict';
import {directionAudit} from './exp313-direction-audit.mjs';
const r=(originClose,point,actual)=>({originClose,point,actual});
test('flat baseline scores 0 direction on moves and abstains',()=>{
 const d=directionAudit([r(100,100,101),r(100,100,99)]);
 assert.equal(d.legacyDirectionAccuracy,0);assert.equal(d.actionCoveragePct,0);assert.equal(d.actionableHitRatePct,null);
});
test('epsilon forecast games legacy score with trivial MAE change',()=>{
 const d=directionAudit(Array.from({length:100},()=>r(100,100.0001,101)));
 assert.equal(d.legacyDirectionAccuracy,100);assert.ok(Math.abs(d.mae-.9999)<1e-10);
});
test('neutral zone prevents epsilon wiggle being actionable',()=>{
 const d=directionAudit([r(100,100.0001,101),r(100,99.9999,99)],{relativeTolerance:.0001});
 assert.equal(d.actionCoveragePct,0);assert.equal(d.actionableHitRatePct,null);
});
test('imbalanced always-up yields 90% hits but 50% balanced recall',()=>{
 const d=directionAudit([...Array.from({length:90},()=>r(100,100.01,101)),...Array.from({length:10},()=>r(100,100.01,99))]);
 assert.equal(d.actionableHitRatePct,90);assert.equal(d.balancedRecallPct,50);
});
test('perfect up/down gets 100% balanced recall',()=>{
 const d=directionAudit([r(100,101,102),r(100,99,98)]);
 assert.equal(d.balancedRecallPct,100);
});
test('no down class leaves balanced recall undefined',()=>{
 assert.equal(directionAudit([r(100,101,102)]).balancedRecallPct,null);
});
test('balanced alternating series has equal MAE but radically different legacy score',()=>{
 const rows=Array.from({length:100},(_,i)=>r(100,100.01,i%2?99:101));
 const a=directionAudit(rows),b=directionAudit(rows.map(x=>({...x,point:100})));
 assert.ok(Math.abs(a.mae-b.mae)<1e-10);assert.equal(a.legacyDirectionAccuracy,50);assert.equal(b.legacyDirectionAccuracy,0);
});
test('relative tolerance is scale invariant',()=>{
 const rows=[r(100,100.01,101),r(100,99.99,99)];
 const a=directionAudit(rows,{relativeTolerance:.0002});
 const b=directionAudit(rows.map(x=>r(x.originClose*50,x.point*50,x.actual*50)),{relativeTolerance:.0002});
 assert.deepEqual(a.confusionActualRows,b.confusionActualRows);
});
test('reject invalid inputs',()=>{
 assert.throws(()=>directionAudit([]),/No evaluation/);
 assert.throws(()=>directionAudit([r(0,1,2)]),/Invalid evaluation/);
 assert.throws(()=>directionAudit([r(100,NaN,101)]),/Invalid evaluation/);
 assert.throws(()=>directionAudit([r(100,101,102)],{relativeTolerance:-1}),/Invalid neutral/);
});
test('SEO visits transfer: 70% legacy hit, 50% balanced recall',()=>{
 const rows=Array.from({length:1000},(_,i)=>r(500,500.01,i%10<7?550:450));
 const d=directionAudit(rows);
 assert.equal(d.legacyDirectionAccuracy,70);assert.equal(d.balancedRecallPct,50);
});

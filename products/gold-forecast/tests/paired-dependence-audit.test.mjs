import test from 'node:test';
import assert from 'node:assert/strict';
import {pairedDependenceAudit} from '../paired-dependence-audit.mjs';
const day=i=>new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10);
function windows(diff){return diff.map((d,i)=>({
  origin_date:day(i*2),target_date:day(i*2+1),actual:100,
  baseline:110,candidate:100+10-d,
  baseline_abs_error:10,candidate_abs_error:10-d
}));}
test('independent hand-computable IID SE and lag zero',()=>{
  const a=pairedDependenceAudit(windows([1,2,3,4]),{minimumWindows:2,lag:0});
  assert.equal(a.n,4);assert.equal(a.mean_improvement,2.5);
  assert.ok(Math.abs(a.iid_standard_error-Math.sqrt(5/12))<1e-12);
  assert.ok(Math.abs(a.hac_standard_error-Math.sqrt(5/16))<1e-12);
  assert.equal(a.claim_of_skill,false);
});
test('positive serial correlation inflates HAC SE and reverses naive nominal z',()=>{
  const a=pairedDependenceAudit(windows([2,-1,2,-1,2,-1,2,-1].flatMap(x=>Array(5).fill(x))),{lag:4});
  assert.equal(a.status,'diagnostic_only');
  assert.ok(a.iid_nominal_z>1.96);
  assert.ok(a.hac_nominal_z<1.96);
  assert.ok(a.hac_to_iid_se_ratio>1.3);
});
test('negative serial correlation can reduce HAC SE, not always inflate',()=>{
  const a=pairedDependenceAudit(windows(Array.from({length:40},(_,i)=>i%2? -1:1)),{lag:3});
  assert.ok(a.hac_standard_error<a.iid_standard_error);
});
test('minimum count blocks any nominal z and skill verdict',()=>{
  const a=pairedDependenceAudit(windows([1,2,3]),{minimumWindows:20});
  assert.equal(a.status,'insufficient_windows');assert.equal(a.hac_nominal_z,undefined);
  assert.equal(a.claim_of_skill,false);
});
test('zero-variance difference is degenerate, not infinite evidence',()=>{
  const a=pairedDependenceAudit(windows(Array(30).fill(1)));
  assert.equal(a.status,'degenerate_variance');assert.equal(a.hac_nominal_z,null);
});
test('candidate worse yields negative mean improvement',()=>{
  const a=pairedDependenceAudit(windows(Array.from({length:30},(_,i)=>-1+(i%2)*.1)));
  assert.ok(a.mean_improvement<0);
});
test('reject overlapping windows',()=>{
  const w=windows([1,2,3]);w[1].origin_date=w[0].origin_date;
  assert.throws(()=>pairedDependenceAudit(w),/Overlapping/);
});
test('reject corrupted stored loss even if prices valid',()=>{
  const w=windows([1,2,3]);w[0].candidate_abs_error=0;
  assert.throws(()=>pairedDependenceAudit(w),/Inconsistent/);
});
test('reject invalid dates and target before origin',()=>{
  const w=windows([1,2,3]);w[0].origin_date='2025-02-30';
  assert.throws(()=>pairedDependenceAudit(w),/Invalid ISO/);
  const x=windows([1,2,3]);x[0].target_date=x[0].origin_date;
  assert.throws(()=>pairedDependenceAudit(x),/target order/);
});
test('reject invalid price, lag and minimum',()=>{
  const w=windows([1,2,3,4]);w[0].actual=NaN;
  assert.throws(()=>pairedDependenceAudit(w),/Invalid price/);
  assert.throws(()=>pairedDependenceAudit(windows([1,2,3,4]),{lag:4,minimumWindows:2}),/Invalid lag/);
  assert.throws(()=>pairedDependenceAudit([], {minimumWindows:1}),/minimumWindows/);
});
test('empty input returns insufficient, not success',()=>{
  const a=pairedDependenceAudit([]);
  assert.equal(a.n,0);assert.equal(a.mean_improvement,null);
});

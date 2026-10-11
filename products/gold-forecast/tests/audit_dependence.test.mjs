import test from 'node:test';
import assert from 'node:assert/strict';
import {auditDependence} from '../audit_dependence.mjs';
const rows=(n=260,kind='trend')=>Array.from({length:n},(_,i)=>({date:new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10),price:kind==='flat'?2000:2000+i*.8+10*Math.sin(i*.5)}));
for(const h of [1,7,30]){
  test(`exact audit count and overlap diagnostics h=${h}`,()=>{
    const r=auditDependence(rows(),h);
    const expected=260-h+1-Math.floor(260*.8);
    assert.equal(r.nAudit,expected);
    assert.equal(r.maxDisjointTargetWindows,Math.ceil(expected/h));
    assert.ok(r.literalCoverage>=0&&r.literalCoverage<=100);
    assert.ok(r.phaseCoverageMin<=r.literalCoverage+1e-9);
    assert.ok(r.phaseCoverageMax+1e-9>=r.literalCoverage);
    for(const p of r.phases)for(let j=1;j<p.origins.length;j++){
      assert.ok(p.origins[j]>=p.origins[j-1]+h);
      assert.ok(p.origins[j]>p.targets[j-1]);
    }
  });
}
test('30-session audit on 260 points has at most ONE disjoint target window',()=>{
  const r=auditDependence(rows(),30);
  assert.equal(r.nAudit,23);
  assert.equal(r.maxDisjointTargetWindows,1);
  assert.equal(r.auditInterpretation,'descriptive_only');
});
test('7-session audit on 260 points has only SEVEN disjoint windows',()=>{
  const r=auditDependence(rows(),7);
  assert.equal(r.nAudit,46);
  assert.equal(r.maxDisjointTargetWindows,7);
  assert.equal(r.auditInterpretation,'descriptive_only');
});
test('one-session audit can pass target-disjoint gate, without independence claim',()=>{
  const r=auditDependence(rows(),1);
  assert.equal(r.nAudit,52);
  assert.equal(r.maxDisjointTargetWindows,52);
  assert.equal(r.auditInterpretation,'eligible_for_further_dependence_checks');
  assert.match(r.caveat,/do not establish statistical independence/);
});
test('flat-series counterexample: no phase disagreement',()=>{
  for(const h of [1,7,30]){
    const r=auditDependence(rows(260,'flat'),h);
    assert.equal(r.literalCoverage,100);
    assert.equal(r.phaseCoverageMin,100);
    assert.equal(r.phaseCoverageMax,100);
  }
});
test('guard against unsupported horizon and invalid threshold',()=>{
  assert.throws(()=>auditDependence(rows(),5));
  assert.throws(()=>auditDependence(rows(),7,0));
});
test('extra 30-session history makes 20 disjoint target windows possible, not proven independent',()=>{
  const r=auditDependence(rows(3400),30);
  assert.ok(r.maxDisjointTargetWindows>=20);
  assert.equal(r.auditInterpretation,'eligible_for_further_dependence_checks');
});

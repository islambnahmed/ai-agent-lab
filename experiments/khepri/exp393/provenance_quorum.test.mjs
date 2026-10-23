import test from 'node:test';
import assert from 'node:assert/strict';
import {corroborate,benchmark} from './provenance_quorum.mjs';
const r=(source,upstream,value)=>({source,upstream,value});
test('two mirrors from same upstream cannot constitute independent quorum',()=>{
 const obs=[r('a1','a',118),r('a2','a',118)];
 assert.equal(corroborate(obs).status,'abstain');
 assert.equal(corroborate(obs,{trustLineage:false}).status,'corroborated_not_verified');
});
test('two independent matching providers corroborate',()=>{
 const out=corroborate([r('a','a',100),r('b','b',100.2)]);
 assert.equal(out.status,'corroborated_not_verified');assert.equal(out.independentGroups,2);
});
test('nontransitive bridge abstains rather than chaining',()=>{
 const out=corroborate([r('a','a',100),r('b','b',100.8),r('c','c',101.6)]);
 assert.equal(out.reason,'ambiguous_equal_quorums');
});
test('a divergent same-upstream mirror quarantines that group',()=>{
 const out=corroborate([r('a1','a',100),r('a2','a',110),r('b','b',100)]);
 assert.equal(out.reason,'insufficient_independent_groups');assert.deepEqual(out.quarantined,['a']);
});
test('unknown lineage fails closed',()=>assert.throws(()=>corroborate([r('a','',100),r('b','b',100)]),/unknown upstream/));
test('independent majority can reject bad mirror upstream',()=>{
 const out=corroborate([r('a1','a',118),r('a2','a',118),r('b','b',100),r('c','c',100)]);
 assert.equal(out.value,100);assert.equal(out.independentGroups,2);
});
test('shared systemic fault cannot be detected by agreement alone',()=>{
 const out=corroborate([r('a','a',118),r('b','b',118),r('c','c',118)],{quorum:3});
 assert.equal(out.value,118); // true value may be 100: counterexample
});
test('three-lineage quorum trades coverage for fewer false accepts',()=>{
 const b=benchmark();
 assert.equal(Object.values(b.methods.lineage3).reduce((a,v)=>a+v,0),b.trials);
 assert.ok(b.methods.lineage3.acceptedWrong<b.methods.lineage2.acceptedWrong);
 assert.ok(b.methods.lineage3.abstained>b.methods.lineage2.abstained);
});
test('benchmark deterministic',()=>assert.deepEqual(benchmark({trials:100}),benchmark({trials:100})));
test('rejects malformed values and invalid quorum',()=>{
 assert.throws(()=>corroborate([r('a','a',NaN)]),/Invalid observation/);
 assert.throws(()=>corroborate([],{quorum:1}),/Invalid corroboration/);
});
test('SEO negative anomaly transfer still exposes shared faults',()=>{
 const b=benchmark({trials:2000,seed:394,baseline:100,amplitude:10,faultMultiplier:0.7});
 assert.ok(b.methods.lineage3.acceptedWrong>0);
 assert.ok(b.methods.lineage3.acceptedWrong<b.methods.lineage2.acceptedWrong);
});

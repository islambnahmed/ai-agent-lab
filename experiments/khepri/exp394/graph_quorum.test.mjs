import test from 'node:test';
import assert from 'node:assert/strict';
import {corroborateGraph,graphFor} from './graph_quorum.mjs';
import {corroborate} from '../exp393/provenance_quorum.mjs';
import {simulate} from './benchmark.mjs';
const obs=(ids,vals)=>ids.map((id,i)=>({source:'feed-'+id,node:id,value:vals[i]}));
test('shared-root mirrors cannot manufacture quorum of 3',()=>{
  const result=corroborateGraph(obs(['X1','X2','X3','Y','Z'],[118,118,118,100,100]),graphFor('honest'));
  assert.equal(result.status,'abstain');
});
test('flat one-hop baseline is fooled by three shared-root mirrors',()=>{
  const observations=obs(['X1','X2','X3','Y','Z'],[118,118,118,100,100]).map(x=>({...x,upstream:x.node}));
  assert.equal(corroborate(observations,{quorum:3}).value,118);
});
test('honest unanimous independent roots still pass',()=>{
  const r=corroborateGraph(obs(['X1','X2','X3','Y','Z'],[100,100,100,100,100]),graphFor('honest'));
  assert.equal(r.status,'corroborated_not_verified'); assert.equal(r.independentGroups,3);
});
test('duplicate feed IDs rejected',()=>assert.throws(()=>corroborateGraph([
  {source:'same',node:'X1',value:100},{source:'same',node:'Y',value:100}],graphFor('honest'))));
test('unknown graph parent rejected',()=>assert.throws(()=>corroborateGraph([], [{id:'A',parents:['missing']}])));
test('cycle rejected even when disconnected',()=>assert.throws(()=>corroborateGraph([], [{id:'A',parents:['B']},{id:'B',parents:['A']}])));
test('duplicate node IDs rejected',()=>assert.throws(()=>corroborateGraph([], [{id:'A',parents:[]},{id:'A',parents:[]}])));
test('inconsistent observations from same lineage quarantined',()=>{
  const r=corroborateGraph(obs(['X1','X2','Y','Z'],[100,120,100,100]),graphFor('honest'));
  assert.equal(r.status,'abstain'); assert.equal(r.quarantined.length,1);
});
test('multiple roots of a merged source block double counting',()=>{
  const g=[{id:'A',parents:[]},{id:'B',parents:[]},{id:'C',parents:[]},{id:'AB',parents:['A','B']}];
  const r=corroborateGraph(obs(['A','B','AB','C'],[100,100,100,100]),g,{quorum:3});
  assert.equal(r.status,'corroborated_not_verified');assert.equal(r.independentGroups,3);
});
test('nontransitive tolerance chain does not become consensus',()=>{
  const g=[{id:'A',parents:[]},{id:'B',parents:[]},{id:'C',parents:[]}];
  const r=corroborateGraph(obs(['A','B','C'],[100,100.7,101.4]),g,{quorum:3,tolerance:0.01});
  assert.equal(r.status,'abstain');
});
test('honest shared-root graph improves false acceptance on gold synthetic case',()=>{
  const r=simulate({trials:2000,seed:394});
  assert.ok(r.metrics.graph.wrong<r.metrics.flat.wrong);
});
test('transfer to SEO negative faults',()=>{
  const r=simulate({trials:2000,seed:395,base:100,amplitude:10,badMultiplier:0.7});
  assert.ok(r.metrics.graph.wrong<r.metrics.flat.wrong);
});
test('forged independence defeats graph quorum: no magic verification',()=>{
  const r=simulate({trials:2000,seed:394,mode:'forged'});
  assert.deepEqual(r.metrics.graph,r.metrics.flat);
});
test('independent control: graph and baseline match',()=>{
  const r=simulate({trials:2000,seed:394,mode:'independent'});
  assert.deepEqual(r.metrics.graph,r.metrics.flat);
});
test('input validation guards NaN and unknown nodes',()=>{
  assert.throws(()=>corroborateGraph([{source:'s',node:'X1',value:NaN}],graphFor('honest')));
  assert.throws(()=>corroborateGraph([{source:'s',node:'unknown',value:100}],graphFor('honest')));
});

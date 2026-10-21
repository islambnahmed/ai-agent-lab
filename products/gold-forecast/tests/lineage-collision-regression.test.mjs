import test from 'node:test';
import assert from 'node:assert/strict';
import {assessLineageConsensus} from '../lineage-consensus.mjs';
const at='2026-10-21T03:00:00Z', cv='XAUUSD:spot:USD/troy_oz:mid';
const roster=(roots)=>roots.map((root,i)=>({provider:'p'+i,root,evidenceRef:'audit',auditedAt:'2026-10-20T00:00:00Z',convention:cv}));
const quotes=(prices)=>prices.map((price,i)=>({provider:'p'+i,price,observedAt:at,convention:cv}));
test('ambiguous clusters with delimiter-bearing root IDs abstain',()=>{
 const roots=['a','b\\u0000c','a\\u0000b','c'].map(x=>x.replace('\\u0000','\u0000'));
 const result=assessLineageConsensus(quotes([100,100,110,110]),roster(roots),{originAt:at,minIndependentRoots:2,minRosterCoverage:1});
 assert.equal(result.reason,'ambiguous_clusters');
});
test('special provider IDs retain exclusion evidence',()=>{
 const r=roster(['a','b','c','d','e']);
 r.push({provider:'__proto__',root:'z',evidenceRef:'audit',auditedAt:'2026-10-20T00:00:00Z',convention:cv});
 const result=assessLineageConsensus(quotes([100,100,100,100,100]),r,{originAt:at,minRosterCoverage:0.5});
 assert.equal(Object.hasOwn(result.excluded,'__proto__'),true);
 assert.equal(result.excluded['__proto__'],'missing_quote');
});

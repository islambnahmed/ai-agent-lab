import test from 'node:test';
import assert from 'node:assert/strict';
import {auditPayload} from './probe.mjs';
import {hash} from '../../../products/gold-forecast/journal.mjs';
const iso=(d)=>d.toISOString().slice(0,10);
const start=new Date('2025-04-01T00:00:00Z');
const points=Array.from({length:175},(_,i)=>({t:iso(new Date(start.getTime()+i*86400000))+'T00:00:00Z',price:4000+i}));
const originDate=points[165].t.slice(0,10);
const base={schemaVersion:1,issuedAt:'2025-09-14T12:00:00Z',source:'Standard Bullion',
 sourceManifest:{url:'https://standardbullion.com/api/v1/market/history?metal=XAU&range=1y'},
 horizon:7,calendar:'observations',targetDate:null,originDate,originClose:4165,
 historyHash:'abc',historyLength:166,point:4200,baseline:4165};
const receipt={...base,id:hash(base)};
const payload={metal:'XAU',unit:'USD per troy ounce',grain:'daily',attribution:'Data by Standard Bullion',points};
const asOf='2025-09-25T12:00:00Z';
test('7th observed close, not guessed calendar date',()=>{
 const x=auditPayload(receipt,payload,asOf);
 assert.equal(x.status,'tentative_current_vintage');
 assert.equal(x.targetDate,points[172].t.slice(0,10));
 assert.equal(x.targetCloseNow,4172);
 assert.equal(x.winner,'baseline');
 assert.equal(x.observationIndexAfterOrigin,7);
});
test('revised origin must fail closed',()=>{
 const changed={...payload,points:points.map((p,i)=>i===165?{...p,price:5000}:p)};
 const x=auditPayload(receipt,changed,asOf);
 assert.equal(x.status,'inconclusive');assert.equal(x.reason,'origin_close_mismatch');
});
test('missing origin does not substitute another date',()=>{
 const changed={...payload,points:points.filter((p,i)=>i!==165)};
 const x=auditPayload(receipt,changed,asOf);
 assert.equal(x.status,'inconclusive');assert.equal(x.reason,'origin_not_in_current_window');
});
test('insufficient future closes is pending',()=>{
 const changed={...payload,points:points.slice(0,170)};
 const x=auditPayload(receipt,changed,'2025-09-19T12:00:00Z');
 assert.equal(x.status,'pending');assert.equal(x.futureObservationCount,4);
});
test('current UTC date is excluded as provisional',()=>{
 const changed={...payload,points:points.slice(0,173)};
 const x=auditPayload(receipt,changed,points[172].t.slice(0,10)+'T12:00:00Z');
 assert.equal(x.status,'pending');assert.equal(x.reason,'insufficient_future_observations');
});
test('reject wrong source unit and downsampled cadence',()=>{
 assert.throws(()=>auditPayload(receipt,{...payload,unit:'USD/gram'},asOf));
 const downPoints=Array.from({length:170},(_,i)=>({t:iso(new Date(Date.parse('2025-01-01T00:00:00Z')+i*2*86400000))+'T00:00:00Z',price:4100+i}));
 const down={...payload,points:downPoints};
 const afterLast=iso(new Date(Date.parse(downPoints.at(-1).t)+86400000))+'T12:00:00Z';
 assert.throws(()=>auditPayload(receipt,down,afterLast),/downsampled/);
});
test('receipt tampering is detected',()=>{
 assert.throws(()=>auditPayload({...receipt,point:1},payload,asOf));
});

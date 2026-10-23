import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {hash} from '../../../products/gold-forecast/journal.mjs';
import {verifyAndPrepareOutcome} from './verified_settlement.mjs';

const day=i=>new Date(Date.UTC(2026,0,1+i)).toISOString().slice(0,10);
const all=Array.from({length:175},(_,i)=>({date:day(i),price:4000+i}));
const vintage=all.slice(0,165);
const url='https://standardbullion.com/api/v1/market/history?metal=XAU&range=1y';
const core={schemaVersion:1,issuedAt:'2026-06-15T12:00:00Z',source:'Standard Bullion',codeCommit:'a'.repeat(40),
  sourceManifest:{url},horizon:7,originDate:day(164),historyHash:hash(vintage),historyLength:165,
  targetDate:null,point:4180,baseline:4164,lower:4000,upper:4300};
const receipt={...core,id:hash(core)};
const history={metal:'XAU',unit:'USD per troy ounce',grain:'daily',attribution:'synthetic fixture',points:all};
const raw=Buffer.from(JSON.stringify(history));
const manifest={status:'fetched',httpStatus:200,url,receivedAt:'2026-06-25T10:00:00Z',rawSha256:createHash('sha256').update(raw).digest('hex')};
const args={receipt,rawBytes:raw,parsedHistory:history,manifest,originalVintage:vintage,
  anchorAt:'2026-06-15T13:00:00Z',observedAt:'2026-06-25T12:00:00Z'};
const run=overrides=>verifyAndPrepareOutcome({...args,...overrides});

test('locks the seventh observed close, not a guessed calendar target',()=>{
  const result=run();assert.equal(result.status,'ready_to_lock');
  assert.equal(result.outcome.targetDate,day(171));assert.equal(result.outcome.actual,4171);
  assert.equal(result.lock.evidence.rawSha256,manifest.rawSha256);
});
test('tampered raw bytes are rejected',()=>assert.throws(()=>run({rawBytes:Buffer.concat([raw,Buffer.from(' ')])}),/SHA-256 mismatch/));
test('parsed copy inconsistent with raw is rejected',()=>assert.throws(()=>run({parsedHistory:{...history,points:all.slice(0,-1)}}),/Parsed history differs/));
test('outcome cannot be settled without frozen original vintage',()=>assert.throws(()=>run({originalVintage:[]}),/Original issue-time vintage/));
test('original overlapping price revision quarantines',()=>{
  const changed=all.map((x,i)=>i===164?{...x,price:x.price+1}:x);
  const payload={...history,points:changed},bytes=Buffer.from(JSON.stringify(payload));
  const m={...manifest,rawSha256:createHash('sha256').update(bytes).digest('hex')};
  assert.throws(()=>run({rawBytes:bytes,parsedHistory:payload,manifest:m}),/Historical vintage revised/);
});
test('manifest from wrong endpoint is rejected',()=>assert.throws(()=>run({manifest:{...manifest,url:'https://example.com'}}),/manifest does not match/));
test('source revision after target remains pending if fewer than 7 new observations',()=>{
  const short={...history,points:all.slice(0,170)};
  const bytes=Buffer.from(JSON.stringify(short));
  const m={...manifest,rawSha256:createHash('sha256').update(bytes).digest('hex')};
  assert.equal(run({rawBytes:bytes,parsedHistory:short,manifest:m}).status,'pending');
});
test('same-day anchor cannot be used to certify an outcome',()=>assert.throws(()=>run({anchorAt:'2026-06-21T01:00:00Z'}),/Same-day target/));
test('tampered receipt id is rejected before settlement',()=>assert.throws(()=>run({receipt:{...receipt,id:'b'.repeat(64)}}),/Receipt integrity mismatch/));

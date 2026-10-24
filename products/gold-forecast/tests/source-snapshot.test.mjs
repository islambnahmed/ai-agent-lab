import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {loadVerifiedHistory} from '../scripts/source_snapshot.mjs';

function fixture(body, overrides={}){
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'gold-source-integrity-'));
  fs.mkdirSync(path.join(root,'data'));
  fs.writeFileSync(path.join(root,'data','history.json'),body);
  const manifest={history:{status:'fetched',receivedAt:'2026-10-12T17:10:55Z',
    rawSha256:createHash('sha256').update(body).digest('hex'),...overrides}};
  fs.writeFileSync(path.join(root,'data','fetch-manifest.json'),JSON.stringify(manifest));
  return root;
}

const raw=Buffer.from('{\n "metal": "XAU", "points": [1, 2]\n}\n');

test('valid snapshot preserves exact byte identity',t=>{
  const root=fixture(raw);t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  assert.deepEqual(loadVerifiedHistory(root).history,{metal:'XAU',points:[1,2]});
});

test('re-serialized but semantically identical JSON is rejected',t=>{
  const root=fixture(raw);t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  fs.writeFileSync(path.join(root,'data','history.json'),'{"metal":"XAU","points":[1,2]}');
  assert.throws(()=>loadVerifiedHistory(root),/differ from fetch manifest/);
});

test('changed valid price history is rejected',t=>{
  const root=fixture(raw);t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  fs.writeFileSync(path.join(root,'data','history.json'),'{"metal":"XAU","points":[1,999]}');
  assert.throws(()=>loadVerifiedHistory(root),/differ from fetch manifest/);
});

test('failed or malformed manifest cannot reuse stale history',t=>{
  for(const overrides of [{status:'unavailable'},{rawSha256:'0'.repeat(63)},{receivedAt:null}]){
    const root=fixture(raw,overrides);t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
    assert.throws(()=>loadVerifiedHistory(root),/lacks a valid fetched manifest/);
  }
});

test('missing historical source fails closed',t=>{
  const root=fixture(raw);t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  fs.unlinkSync(path.join(root,'data','history.json'));
  assert.throws(()=>loadVerifiedHistory(root),/ENOENT/);
});

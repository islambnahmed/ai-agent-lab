import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {readVerifiedSnapshot} from '../snapshot-integrity.mjs';

const digest=x=>createHash('sha256').update(x).digest('hex');
const url='https://standardbullion.com/api/v1/market/history?metal=XAU&range=1y';
function fixture(t){
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'gold-snapshot-'));
  t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const bytes=Buffer.from('{"metal":"XAU","points":[{"date":"2025-01-01","price":2500}]}');
  fs.writeFileSync(path.join(dir,'history.json'),bytes);
  const manifest={history:{status:'fetched',url,rawSha256:digest('raw response'),storedSha256:digest(bytes)}};
  return {dir,bytes,manifest};
}
test('accepts exactly the saved snapshot named by the manifest',t=>{
  const {dir,manifest}=fixture(t);
  assert.equal(readVerifiedSnapshot(dir,'history',manifest,{expectedUrl:url}).metal,'XAU');
});
test('detects altered payload even if JSON still parses',t=>{
  const {dir,manifest}=fixture(t);
  fs.appendFileSync(path.join(dir,'history.json'),'\n');
  assert.throws(()=>readVerifiedSnapshot(dir,'history',manifest,{expectedUrl:url}),/differs/);
});
test('rejects absent stored hash and unsuccessful fetch',t=>{
  const {dir,manifest}=fixture(t);
  delete manifest.history.storedSha256;
  assert.throws(()=>readVerifiedSnapshot(dir,'history',manifest,{expectedUrl:url}),/manifest/);
  manifest.history.storedSha256=digest(fs.readFileSync(path.join(dir,'history.json')));
  manifest.history.status='unavailable';
  assert.throws(()=>readVerifiedSnapshot(dir,'history',manifest,{expectedUrl:url}),/manifest/);
});
test('rejects a different source URL and unsupported snapshot names',t=>{
  const {dir,manifest}=fixture(t);
  assert.throws(()=>readVerifiedSnapshot(dir,'history',manifest,{expectedUrl:url+'evil'}),/URL/);
  assert.throws(()=>readVerifiedSnapshot(dir,'spot',manifest),/Unsupported/);
});
test('rejects truncated or malformed JSON even with matching digest',t=>{
  const {dir,manifest}=fixture(t);
  fs.writeFileSync(path.join(dir,'history.json'),'{');
  manifest.history.storedSha256=digest('{');
  assert.throws(()=>readVerifiedSnapshot(dir,'history',manifest,{expectedUrl:url}),SyntaxError);
});

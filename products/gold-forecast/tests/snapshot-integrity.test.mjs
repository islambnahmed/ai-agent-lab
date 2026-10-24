import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {parseVerifiedSnapshot} from '../snapshot-integrity.mjs';

const sha = b => createHash('sha256').update(b).digest('hex');
const body = Buffer.from('{"metal":"XAU","points":[1,2]}');
const meta = {status:'fetched',httpStatus:200,rawSha256:sha(Buffer.from('original HTTP body')),
  storedSha256:sha(body)};

test('stored snapshot is bound to its own manifest, not raw HTTP hash',()=>{
  assert.deepEqual(parseVerifiedSnapshot(body,meta,'history'),{metal:'XAU',points:[1,2]});
  assert.notEqual(meta.rawSha256,meta.storedSha256);
});

test('tampered or swapped local snapshots are rejected before evaluation or issuance',()=>{
  assert.throws(()=>parseVerifiedSnapshot(Buffer.from('{"metal":"XAG"}'),meta,'history'),/differs/);
  assert.throws(()=>parseVerifiedSnapshot(Buffer.from(body.toString()+' '),meta,'history'),/differs/);
});

test('failed, legacy, and malformed manifests fail closed',()=>{
  for(const changed of [
    {...meta,status:'unavailable'}, {...meta,httpStatus:404},
    {...meta,storedSha256:undefined}, {...meta,rawSha256:'invalid'},
    undefined
  ]) assert.throws(()=>parseVerifiedSnapshot(body,changed,'history'),/integrity-tagged/);
});

test('a matching digest does not waive JSON parsing',()=>{
  const bad=Buffer.from('{invalid');
  assert.throws(()=>parseVerifiedSnapshot(bad,{...meta,storedSha256:sha(bad)}),SyntaxError);
});

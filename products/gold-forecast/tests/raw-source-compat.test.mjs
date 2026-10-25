import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {parseVerifiedHistorySnapshot} from '../journal.mjs';

const raw=Buffer.from('{\\n "metal":"XAU", "attribution":"café"\\n}\\n'.replaceAll('\\n','\n'),'utf8');
const digest=createHash('sha256').update(raw).digest('hex');
const manifest={status:'fetched',rawSha256:digest,storedSha256:digest};

test('peer snapshot parser accepts byte-exact raw provider response',()=>{
  assert.deepEqual(parseVerifiedHistorySnapshot(raw,manifest),{metal:'XAU',attribution:'café'});
});

test('peer snapshot parser quarantines altered bytes after fetch',()=>{
  const changed=Buffer.from('{"metal":"XAU","attribution":"café"}','utf8');
  assert.throws(()=>parseVerifiedHistorySnapshot(changed,manifest),/SHA-256 mismatch/);
});

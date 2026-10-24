import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import {hash,verifyReceipt,verifiedVintagePath} from '../journal.mjs';

const directory=path.join('data','vintages');
const signed=changes=>{
  const payload={schemaVersion:1,issuedAt:'2026-10-12T17:12:52Z',
    horizon:1,historyLength:165,historyHash:'a'.repeat(64),
    codeCommit:'b'.repeat(40),...changes};
  return {...payload,id:hash(payload)};
};

test('well-formed receipt yields a path inside the frozen-vintage directory',()=>{
  const receipt=signed({});
  assert.equal(verifyReceipt(receipt),true);
  assert.equal(verifiedVintagePath(directory,receipt),
    path.join(directory,'a'.repeat(64)+'.json'));
});

test('rehashed traversal payload is rejected before any file access',()=>{
  // Prior implementation accepted this because id was internally consistent.
  for(const historyHash of ['../../../../outside/target','../other',
    '/tmp/outside','a'.repeat(63),'A'.repeat(64),'']) {
    const receipt=signed({historyHash});
    assert.throws(()=>verifyReceipt(receipt),/Invalid receipt digest/);
    assert.throws(()=>verifiedVintagePath(directory,receipt),/Invalid receipt digest/);
  }
});

test('rehashed malformed code commit and receipt IDs are rejected',()=>{
  assert.throws(()=>verifyReceipt(signed({codeCommit:'../outside'})),/Invalid receipt digest/);
  assert.throws(()=>verifyReceipt(signed({codeCommit:'A'.repeat(40)})),/Invalid receipt digest/);
  const receipt=signed({});
  receipt.id='not-a-sha';
  assert.throws(()=>verifiedVintagePath(directory,receipt),/Receipt integrity mismatch/);
});

test('missing vintage directory fails without touching the filesystem',()=>{
  assert.throws(()=>verifiedVintagePath('',signed({})),/Vintage directory required/);
  assert.throws(()=>verifiedVintagePath(null,signed({})),/Vintage directory required/);
});

test('unmodified receipt still detects content tampering',()=>{
  const receipt=signed({});
  receipt.historyHash='c'.repeat(64);
  assert.throws(()=>verifiedVintagePath(directory,receipt),/Receipt integrity mismatch/);
});

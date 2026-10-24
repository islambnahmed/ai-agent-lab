import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {evaluateReceiptFile} from '../settlement-file.mjs';

function withFiles(run) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'gold-settlement-'));
  try { return run(dir); } finally { fs.rmSync(dir, {recursive: true, force: true}); }
}

test('valid receipt returns evaluated outcome unchanged', () => withFiles(dir => {
  const filename = path.join(dir, 'valid.json');
  fs.writeFileSync(filename, JSON.stringify({id: 'abc', horizon: 1}));
  assert.deepEqual(evaluateReceiptFile(filename, receipt => ({id: receipt.id, status: 'pending'})),
    {id: 'abc', status: 'pending'});
}));

test('malformed JSON quarantines only that file, allowing a later file to succeed', () => withFiles(dir => {
  const bad = path.join(dir, 'bad.json');
  const good = path.join(dir, 'good.json');
  fs.writeFileSync(bad, '{oops');
  fs.writeFileSync(good, JSON.stringify({id: 'ok', horizon: 7}));
  const outcomes = [bad, good].map(file => evaluateReceiptFile(file, receipt =>
    ({id: receipt.id, horizon: receipt.horizon, status: 'pending'})));
  assert.equal(outcomes[0].status, 'quarantined');
  assert.equal(outcomes[0].file, 'bad.json');
  assert.equal(outcomes[0].id, null);
  assert.equal(outcomes[1].status, 'pending');
  assert.equal(outcomes[1].id, 'ok');
}));

test('unreadable or removed receipt file quarantines instead of aborting batch', () => withFiles(dir => {
  const outcome = evaluateReceiptFile(path.join(dir, 'missing.json'), () => {
    throw Error('Should not evaluate missing receipt');
  });
  assert.equal(outcome.status, 'quarantined');
  assert.equal(outcome.file, 'missing.json');
}));

test('invalid receipt evaluation is quarantined with safe metadata', () => withFiles(dir => {
  const filename = path.join(dir, 'invalid.json');
  fs.writeFileSync(filename, JSON.stringify({id: 'receipt', horizon: 30}));
  const outcome = evaluateReceiptFile(filename, () => { throw Error('Receipt integrity mismatch'); });
  assert.deepEqual(outcome, {id: 'receipt', horizon: 30, file: 'invalid.json',
    status: 'quarantined', error: 'Receipt integrity mismatch'});
}));

test('programming misuse of evaluator API is not silently quarantined', () => withFiles(dir => {
  assert.throws(() => evaluateReceiptFile(path.join(dir, 'any.json'), null), /Receipt evaluator required/);
}));

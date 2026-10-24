import test from 'node:test';
import assert from 'node:assert/strict';
import {issueReceipt, settleReceipt} from '../journal.mjs';

// All observations are synthetic. No real provider data or forecast-skill claim.
const history = Array.from({length:260}, (_, i) => ({
  date: new Date(Date.UTC(2026, 0, 1 + i)).toISOString().slice(0, 10),
  price: 2500 + i * 0.7 + 3 * Math.sin(i * 0.17)
}));
const outcome = [...history, {date: '2026-09-18', price: 2700}];
const options = issuedAt => ({
  issuedAt,
  source: 'synthetic-test-only',
  codeCommit: '0'.repeat(40),
  sourceManifest: {receivedAt: '2026-09-18T00:15:00Z'}
});
const receipt = issueReceipt(history, 1, options('2026-09-18T00:30:00Z'));

test('equivalent UTC and negative-offset settlement instants produce identical matured outcomes', () => {
  assert.equal(receipt.targetDate, '2026-09-18');
  const utc = settleReceipt(receipt, outcome, {asOf:'2026-09-19T02:30:00Z'});
  const offset = settleReceipt(receipt, outcome, {asOf:'2026-09-18T23:30:00-03:00'});
  assert.equal(utc.status, 'matured');
  assert.deepEqual(offset, utc);
});

test('equivalent UTC and positive-offset settlement instants produce identical outcomes', () => {
  const utc = settleReceipt(receipt, outcome, {asOf:'2026-09-19T02:30:00Z'});
  const offset = settleReceipt(receipt, outcome, {asOf:'2026-09-19T08:00:00+05:30'});
  assert.deepEqual(offset, utc);
});

test('completed daily close is pending before UTC midnight and matures at UTC midnight', () => {
  const before = settleReceipt(receipt, outcome, {asOf:'2026-09-18T23:59:59Z'});
  const beforeOffset = settleReceipt(receipt, outcome, {asOf:'2026-09-19T02:59:59+03:00'});
  assert.equal(before.status, 'pending');
  assert.deepEqual(beforeOffset, before);
  const after = settleReceipt(receipt, outcome, {asOf:'2026-09-19T00:00:00Z'});
  const afterOffset = settleReceipt(receipt, outcome, {asOf:'2026-09-18T21:00:00-03:00'});
  assert.equal(after.status, 'matured');
  assert.deepEqual(afterOffset, after);
});

test('equivalent issue timestamps preserve target calendar date and outcome', () => {
  const offsetReceipt = issueReceipt(history, 1, options('2026-09-17T21:30:00-03:00'));
  assert.equal(offsetReceipt.targetDate, receipt.targetDate);
  const settled = settleReceipt(offsetReceipt, outcome, {asOf:'2026-09-19T02:30:00Z'});
  assert.equal(settled.status, 'matured');
  assert.equal(settled.actual, settleReceipt(receipt, outcome, {asOf:'2026-09-19T02:30:00Z'}).actual);
});

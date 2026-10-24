import test from 'node:test';
import assert from 'node:assert/strict';
import {issueReceipt, settleReceipt} from '../journal.mjs';

// Irregular synthetic provider closes: one absent calendar day every 17 observations.
// Dates remain unique, sorted, and no gap exceeds two calendar days.
const date = n => new Date(Date.UTC(2026, 0, 1 + n)).toISOString().slice(0, 10);
const addDays = (d, n) => new Date(Date.parse(d + 'T00:00:00Z') + n * 86400000).toISOString().slice(0, 10);
const rows = Array.from({length:295}, (_, i) => ({
  date: date(i + Math.floor(i / 17)),
  price: 2500 + i * 0.7 + 3 * Math.sin(i * 0.17)
}));
const history = rows.slice(0, 260);
const issuedDay = addDays(history.at(-1).date, 1);
const issuedAt = issuedDay + 'T00:30:00Z';
const options = timestamp => ({
  issuedAt: timestamp,
  source: 'synthetic-irregular-observations-only',
  codeCommit: '0'.repeat(40),
  sourceManifest: {receivedAt: issuedDay + 'T00:15:00Z'}
});

for (const horizon of [1, 7, 30]) {
  const receipt = issueReceipt(history, horizon, options(issuedAt));
  const target = rows[260 + horizon - 1];
  const complete = rows.slice(0, 260 + horizon);
  const after = addDays(target.date, 1) + 'T00:00:00Z';

  test('irregular h' + horizon + ': counts observed closes without inventing target date', () => {
    assert.equal(receipt.calendar, 'observations');
    assert.equal(receipt.targetDate, null);
    assert.equal(receipt.horizon, horizon);
    assert.equal(receipt.historyLength, 260);
    const result = settleReceipt(receipt, complete, {asOf: after});
    assert.equal(result.status, 'matured');
    assert.equal(result.targetDate, target.date);
    assert.equal(result.actual, target.price);
    assert.equal(result.modelAbsError, Math.abs(receipt.point - target.price));
  });

  test('irregular h' + horizon + ': incomplete observation horizon stays pending', () => {
    const incomplete = rows.slice(0, 260 + horizon - 1);
    const result = settleReceipt(receipt, incomplete, {asOf: after});
    assert.equal(result.status, 'pending');
    assert.equal(result.targetDate, null);
  });

  test('irregular h' + horizon + ': observed target stays pending until next UTC day', () => {
    const before = settleReceipt(receipt, complete, {asOf: target.date + 'T23:59:59Z'});
    assert.equal(before.status, 'pending');
    assert.equal(before.targetDate, target.date);
    assert.equal(settleReceipt(receipt, complete, {asOf: after}).status, 'matured');
  });

  test('irregular h' + horizon + ': equivalent timezone instants preserve settlement', () => {
    const shifted = new Date(Date.parse(after) - 3 * 3600000).toISOString().slice(0, 19) + '-03:00';
    assert.deepEqual(settleReceipt(receipt, complete, {asOf: shifted}),
      settleReceipt(receipt, complete, {asOf: after}));
    const alternateIssue = new Date(Date.parse(issuedAt) - 3 * 3600000).toISOString().slice(0, 19) + '-03:00';
    const alternateReceipt = issueReceipt(history, horizon, options(alternateIssue));
    assert.equal(alternateReceipt.calendar, 'observations');
    assert.equal(alternateReceipt.targetDate, null);
    assert.equal(settleReceipt(alternateReceipt, complete, {asOf: after}).actual, target.price);
  });

  test('irregular h' + horizon + ': changed historical vintage is quarantined', () => {
    const revised = complete.map((r, i) => i === 42 ? {...r, price:r.price + 1} : r);
    assert.throws(() => settleReceipt(receipt, revised, {asOf: after}), /vintage revised|prefix missing/i);
  });
}

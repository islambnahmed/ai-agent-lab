import test from 'node:test';
import assert from 'node:assert/strict';
import {issueReceipt, settleReceipt} from '../journal.mjs';

// Entirely synthetic calendar-day closes: no provider data or forecast-skill claim.
const day = n => new Date(Date.UTC(2026, 0, 1 + n)).toISOString().slice(0, 10);
const history = Array.from({length:260}, (_, i) => ({
  date: day(i),
  price: 2500 + i * 0.7 + 3 * Math.sin(i * 0.17)
}));
const issueAt = '2026-09-18T00:30:00Z';
const sourceManifest = {receivedAt:'2026-09-18T00:15:00Z'};
const receiptOptions = issuedAt => ({
  issuedAt, source:'synthetic-horizon-test', codeCommit:'0'.repeat(40), sourceManifest
});
const future = n => Array.from({length:n}, (_, i) => ({
  date: day(260 + i), price:2700 + i * 0.8
}));
const addDays = (date, days) => new Date(Date.parse(date + 'T00:00:00Z') + days * 86400000).toISOString().slice(0,10);

for (const horizon of [7, 30]) {
  const receipt = issueReceipt(history, horizon, receiptOptions(issueAt));
  const complete = [...history, ...future(horizon)];
  const expectedDate = day(259 + horizon);
  const after = addDays(expectedDate, 1) + 'T00:00:00Z';
  const before = expectedDate + 'T23:59:59Z';

  test('h' + horizon + ': calendar target is exact and UTC-offset settlement is invariant', () => {
    assert.equal(receipt.calendar, 'daily');
    assert.equal(receipt.targetDate, expectedDate);
    const result = settleReceipt(receipt, complete, {asOf:after});
    assert.equal(result.status, 'matured');
    assert.equal(result.targetDate, expectedDate);
    assert.equal(result.actual, complete.at(-1).price);
    assert.equal(result.modelAbsError, Math.abs(receipt.point-result.actual));
    assert.equal(result.baselineAbsError, Math.abs(receipt.baseline-result.actual));
    const equivalent = new Date(Date.parse(after) - 3 * 3600000).toISOString().slice(0, 19) + '-03:00';
    // An explicit -03:00 clock reading for the same instant.
    assert.deepEqual(settleReceipt(receipt, complete, {asOf:equivalent}), result);
  });

  test('h' + horizon + ': completed target cannot settle before its UTC day closes', () => {
    const pending = settleReceipt(receipt, complete, {asOf:before});
    assert.equal(pending.status, 'pending');
    assert.equal(pending.targetDate, expectedDate);
    assert.equal(settleReceipt(receipt, complete, {asOf:after}).status, 'matured');
  });

  test('h' + horizon + ': revised historical prefix is quarantined', () => {
    const revised = complete.map((row, i) => i===12 ? {...row,price:row.price+1} : row);
    assert.throws(() => settleReceipt(receipt, revised, {asOf:after}), /vintage revised|prefix missing/i);
  });

  test('h' + horizon + ': missing target is not silently replaced by a later close', () => {
    const missingTarget = [...history, ...future(horizon+1).filter(row => row.date!==expectedDate)];
    const laterAsOf = addDays(expectedDate, 2) + 'T00:00:00Z';
    assert.throws(() => settleReceipt(receipt, missingTarget, {asOf:laterAsOf}), /Target close missing/i);
  });

  test('h' + horizon + ': equivalent issue instant retains target date and outcome', () => {
    const alternate = issueReceipt(history, horizon, receiptOptions('2026-09-17T21:30:00-03:00'));
    assert.equal(alternate.targetDate, receipt.targetDate);
    const result = settleReceipt(receipt, complete, {asOf:after});
    const alternateResult = settleReceipt(alternate, complete, {asOf:after});
    assert.equal(alternateResult.status, 'matured');
    assert.equal(alternateResult.actual, result.actual);
  });
}

import test from 'node:test';
import assert from 'node:assert/strict';
import {issueReceipt, settleReceipt, hash, verifyReceipt} from '../journal.mjs';

const commit = 'a'.repeat(40);
function history() {
  const rows = [];
  let t = Date.parse('2026-10-16T00:00:00Z');
  while (rows.length < 260) {
    const d = new Date(t), weekday = d.getUTCDay();
    if (weekday !== 0 && weekday !== 6) {
      const i = 259 - rows.length;
      rows.push({date:d.toISOString().slice(0,10),price:2400+i*0.8+10*Math.sin(i*.11)});
    }
    t -= 86400000;
  }
  return rows.reverse();
}
const series = history();
const options = (issuedAt, receivedAt) => ({
  issuedAt, source:'synthetic regression fixture', codeCommit:commit,
  sourceManifest:{receivedAt}
});
const unsafeLocal = '2026-10-19T23:30:00-03:00'; // 2026-10-20 02:30 UTC
const unsafeUtc = '2026-10-20T02:30:00Z';
const fetched = '2026-10-20T02:29:00Z';

test('same UTC instant cannot change prospective eligibility through timezone spelling', () => {
  assert.equal(Date.parse(unsafeLocal), Date.parse(unsafeUtc));
  assert.throws(
    () => issueReceipt(series,1,options(unsafeLocal,fetched)),
    /target.*(day|mature|issued|already)|issuance.*target/i
  );
  assert.throws(
    () => issueReceipt(series,1,options(unsafeUtc,fetched)),
    /target.*(day|mature|issued|already)|issuance.*target/i
  );
});

test('even UTC same-day issuance is conservatively refused when close time is unknown', () => {
  assert.throws(
    () => issueReceipt(series,1,options('2026-10-19T10:00:00Z','2026-10-19T09:59:00Z')),
    /target.*(day|mature|issued|already)|issuance.*target/i
  );
});

test('issue before target UTC day remains allowed', () => {
  const receipt = issueReceipt(series,1,options('2026-10-18T12:00:00Z','2026-10-18T11:59:00Z'));
  assert.equal(receipt.targetDate,'2026-10-19');
  assert.equal(verifyReceipt(receipt),true);
});

test('settlement rejects a legacy receipt issued after target UTC day even if local date matches', () => {
  const safe = issueReceipt(series,1,options('2026-10-18T12:00:00Z','2026-10-18T11:59:00Z'));
  const {id:ignored,...body} = safe;
  const legacyBody = {...body,issuedAt:unsafeLocal,sourceManifest:{receivedAt:fetched}};
  const legacy = {...legacyBody,id:hash(legacyBody)};
  assert.equal(verifyReceipt(legacy),true);
  const target = {date:'2026-10-19',price:2700};
  assert.throws(
    () => settleReceipt(legacy,[...series,target],{asOf:'2026-10-21T12:00:00Z'}),
    /outcome.*(predates|issuance|issued|day)|target.*(day|issued|already)/i
  );
});

test('normal pre-target receipt can mature with exact target close', () => {
  const receipt = issueReceipt(series,1,options('2026-10-18T12:00:00Z','2026-10-18T11:59:00Z'));
  const settled = settleReceipt(receipt,[...series,{date:'2026-10-19',price:2700}],{asOf:'2026-10-21T12:00:00Z'});
  assert.equal(settled.status,'matured');
  assert.equal(settled.targetDate,'2026-10-19');
});

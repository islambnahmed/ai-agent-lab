import test from 'node:test';
import assert from 'node:assert/strict';
import {createSuffixCommitment,auditSuffixCommitment,auditLegacyFullHash,digest} from './rolling_vintage.mjs';
const d=i=>new Date(Date.UTC(2026,0,1+i)).toISOString().slice(0,10);
const series=Array.from({length:90},(_,i)=>({date:d(i),price:4000+i*.5}));
const c=createSuffixCommitment(series);
test('full series and appended outcomes preserve full match',()=>{
  const r=auditSuffixCommitment(c,[...series,{date:d(90),price:4046}]);
  assert.equal(r.status,'full_history_match');assert.equal(r.observedAfterOrigin,1);
});
test('rolling window removes earliest dates without inventing revision',()=>{
  const r=auditSuffixCommitment(c,[...series.slice(15),{date:d(90),price:4046}]);
  assert.equal(r.status,'overlap_match_prefix_unverifiable');assert.equal(r.missingOriginalPrefixRows,15);
  assert.equal(r.sufficientOverlap,true);assert.equal(r.certified,false);
});
test('changed price inside observed overlap is detected',()=>{
  const changed=series.slice(10).map(r=>({...r}));changed[24].price+=1;
  assert.equal(auditSuffixCommitment(c,changed).status,'history_values_changed');
});
test('missing interior historical date is not called a price revision',()=>{
  const changed=series.slice(10).filter(r=>r.date!==d(34));
  assert.equal(auditSuffixCommitment(c,changed).status,'history_dates_changed');
});
test('inserted historical date is classified as a date change',()=>{
  const shifted=series.filter(r=>r.date!==d(45));
  const commitment=createSuffixCommitment(shifted);
  assert.equal(auditSuffixCommitment(commitment,series).status,'history_dates_changed');
});
test('no overlap returns indeterminate, not a claim of revision',()=>{
  const future=Array.from({length:40},(_,i)=>({date:d(100+i),price:4100+i}));
  assert.equal(auditSuffixCommitment(c,future).status,'indeterminate_no_overlap');
});
test('short matching overlap is flagged insufficient',()=>{
  const r=auditSuffixCommitment(c,series.slice(-5));
  assert.equal(r.status,'overlap_match_prefix_unverifiable');assert.equal(r.sufficientOverlap,false);
});
test('tampered commitment cannot silently pass',()=>{
  assert.throws(()=>auditSuffixCommitment({...c,originDate:d(88)},series),/Invalid commitment/);
  assert.throws(()=>auditSuffixCommitment({...c,suffixDigests:[...c.suffixDigests.slice(0,-1),'0'.repeat(64)]},series),/integrity/);
});
test('legacy single-hash receipt: full match or inconclusive, never revision claim',()=>{
  const old={originDate:d(89),historyLength:90,historyHash:digest(series)};
  assert.equal(auditLegacyFullHash(old,series).status,'full_history_match');
  assert.equal(auditLegacyFullHash(old,series.slice(1)).status,'indeterminate_legacy_prefix');
  const modified=series.map(r=>({...r}));modified[30].price++;
  assert.equal(auditLegacyFullHash(old,modified).status,'indeterminate_legacy_prefix');
});
test('reject invalid duplicate or unordered current rows',()=>{
  assert.throws(()=>auditSuffixCommitment(c,[series[1],series[0]]),/strictly increasing/);
  assert.throws(()=>createSuffixCommitment([series[0],series[0]]),/strictly increasing/);
});

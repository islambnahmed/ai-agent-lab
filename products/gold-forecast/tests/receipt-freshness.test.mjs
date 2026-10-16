import test from 'node:test';
import assert from 'node:assert/strict';
import {issueReceipt} from '../journal.mjs';

// Integration tests execute the actual receipt issuer and forecast engine,
// not a transcription of its guard. Dates are frozen; no network calls.
const END='2025-12-12'; // Friday
const day=ms=>new Date(ms).toISOString().slice(0,10);
const end=Date.parse(END+'T00:00:00Z');
const daily=Array.from({length:360},(_,i)=>({
  date:day(end-(359-i)*86400000),price:2500+i*.45+Math.sin(i/11)*7
}));
const weekdays=[];
for(let ms=end;weekdays.length<360;ms-=86400000){
  if(![0,6].includes(new Date(ms).getUTCDay()))weekdays.push({date:day(ms),price:2500});
}
weekdays.reverse().forEach((row,i)=>{row.price+=i*.45+Math.sin(i/11)*7;});
const irregular=daily.filter((_,i)=>i!==180);
const options=issuedAt=>({issuedAt,source:'fixture',codeCommit:'a'.repeat(40),
  sourceManifest:{receivedAt:new Date(Date.parse(issuedAt)-60000).toISOString()}});

test('daily origin on Friday may issue on Saturday (next close is still incomplete)',()=>{
  const issuedAt='2025-12-13T12:00:00Z';
  const receipt=issueReceipt(daily,1,options(issuedAt));
  assert.equal(receipt.originDate,END);
  assert.equal(receipt.calendar,'daily');
});
test('daily Friday origin cannot issue on Sunday even with 30-day target in future',()=>{
  const issuedAt='2025-12-14T12:00:00Z';
  assert.throws(()=>issueReceipt(daily,30,options(issuedAt)),/expected close was missed/);
});
test('weekday Friday origin may issue Sunday and Monday before Monday close',()=>{
  for(const issuedAt of ['2025-12-14T12:00:00Z','2025-12-15T12:00:00Z']){
    const receipt=issueReceipt(weekdays,1,options(issuedAt));
    assert.equal(receipt.calendar,'weekdays');
    assert.equal(receipt.originDate,END);
  }
});
test('weekday Friday origin cannot issue Tuesday even with a 30-close target ahead',()=>{
  const issuedAt='2025-12-16T12:00:00Z';
  assert.throws(()=>issueReceipt(weekdays,30,options(issuedAt)),/expected close was missed/);
});
test('irregular origin remains fail-closed after more than one calendar day',()=>{
  const issuedAt='2025-12-14T12:00:00Z';
  assert.throws(()=>issueReceipt(irregular,7,options(issuedAt)),/stale irregular close/);
});
test('timezone-offset issuance is compared by UTC date, not the literal date prefix',()=>{
  // 2025-12-16 00:30 +14 is still 2025-12-15 UTC; Monday close is incomplete.
  const issuedAt='2025-12-16T00:30:00+14:00';
  const receipt=issueReceipt(weekdays,1,options(issuedAt));
  assert.equal(receipt.calendar,'weekdays');
});

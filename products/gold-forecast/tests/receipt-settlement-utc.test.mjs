import test from 'node:test';
import assert from 'node:assert/strict';
import {issueReceipt, settleReceipt} from '../journal.mjs';

const end=Date.parse('2025-12-12T00:00:00Z');
const history=[];
for(let ms=end;history.length<360;ms-=86400000){
  if(![0,6].includes(new Date(ms).getUTCDay()))
    history.push({date:new Date(ms).toISOString().slice(0,10),price:2500});
}
history.reverse().forEach((row,i)=>{row.price+=i*.45+Math.sin(i/11)*7;});
const next=[...history,{date:'2025-12-15',price:history.at(-1).price+1.25}];
const options=issuedAt=>({issuedAt,source:'frozen fixture',codeCommit:'a'.repeat(40),
  sourceManifest:{receivedAt:new Date(Date.parse(issuedAt)-60000).toISOString()}});

test('positive-offset issue uses UTC day for settlement outcome ordering',()=>{
  const receipt=issueReceipt(history,1,options('2025-12-16T00:30:00+14:00'));
  assert.equal(receipt.targetDate,'2025-12-15');
  const result=settleReceipt(receipt,next,{asOf:'2025-12-16T12:00:00Z'});
  assert.equal(result.status,'matured');
});

test('negative-offset settlement uses UTC day for target maturity',()=>{
  const receipt=issueReceipt(history,1,options('2025-12-15T12:00:00Z'));
  const result=settleReceipt(receipt,next,{asOf:'2025-12-15T23:30:00-10:00'});
  assert.equal(result.status,'matured');
});

test('same UTC day stays pending, following UTC day matures',()=>{
  const receipt=issueReceipt(history,1,options('2025-12-15T12:00:00Z'));
  assert.equal(settleReceipt(receipt,next,{asOf:'2025-12-15T18:00:00Z'}).status,'pending');
  assert.equal(settleReceipt(receipt,next,{asOf:'2025-12-16T12:00:00Z'}).status,'matured');
});

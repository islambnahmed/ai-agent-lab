import test from 'node:test';
import assert from 'node:assert/strict';
import {issue,settle} from './prospective_ledger.mjs';
const history=Array.from({length:50},(_,i)=>{
 const date=new Date(Date.UTC(2026,0,1+i)).toISOString().slice(0,10);
 return {date,price:2500+i};
});
const revision='4e4a2438608955e17f3d0e3dd66764aa5cb6c9b4';
test('rolling history window settles using origin date, not row zero',()=>{
 const receipt=issue({series:history.slice(8),horizon:1,model:'persistence',
  modelRevision:revision,issuedAt:'2026-02-20T00:01:00Z',source:'synthetic:rolling'});
 const future={date:'2026-02-23',price:2600};
 const result=settle(receipt,[...history,future]);
 assert.equal(result.status,'matured');
 assert.equal(result.targetDate,'2026-02-23');
});
test('missing a pinned rolling history row rejects settlement',()=>{
 const receipt=issue({series:history.slice(8),horizon:1,model:'persistence',
  modelRevision:revision,issuedAt:'2026-02-20T00:01:00Z',source:'synthetic:rolling'});
 assert.throws(()=>settle(receipt,[...history.slice(9),{date:'2026-02-23',price:2600}]),/Original history missing/);
});

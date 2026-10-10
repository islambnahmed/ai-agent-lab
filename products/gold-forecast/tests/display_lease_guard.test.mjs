import test from "node:test";
import assert from "node:assert/strict";
import {enforceDisplayLease} from "../display_lease_guard.mjs";

const start=Date.parse("2026-10-09T16:00:00Z");
function fixture() {
  const events=[];
  const snapshot={
    loading:false,mode:"live",
    quote:{ask:4200,bid:4190},
    quoteUpdated:"2026-10-09T15:59:00Z",
    historyLatestDate:"2026-10-09",
    series:[{date:"2026-10-09",price:4190}]
  };
  const actions={
    expireQuote:()=>events.push("quote"),
    expireHistory:()=>events.push("history"),
    changeStatus:s=>events.push("state:"+s)
  };
  return {snapshot,actions,events};
}
test("fresh quote and history remain visible",()=>{
  const f=fixture();
  assert.equal(enforceDisplayLease(f.snapshot,f.actions,start).state,"live");
  assert.deepEqual(f.events,[]);
});
test("quote expires without erasing a fresh forecast",()=>{
  const f=fixture();
  enforceDisplayLease(f.snapshot,f.actions,start+16*60000);
  assert.deepEqual(f.events,["quote","state:history-only"]);
  assert.ok(f.snapshot.series);
  assert.equal(f.snapshot.quote,null);
});
test("history expires separately after seven days",()=>{
  const f=fixture();
  enforceDisplayLease(f.snapshot,f.actions,start+16*60000);
  enforceDisplayLease(f.snapshot,f.actions,start+8*86400000);
  assert.deepEqual(f.events,["quote","state:history-only","history","state:unavailable"]);
  assert.equal(f.snapshot.series,null);
});
test("expiry is idempotent",()=>{
  const f=fixture();
  enforceDisplayLease(f.snapshot,f.actions,start+8*86400000);
  enforceDisplayLease(f.snapshot,f.actions,start+8*86400000);
  assert.deepEqual(f.events,["quote","history","state:unavailable"]);
});
test("DEMO and CSV never expire under provider rules",()=>{
  for (const mode of ["demo","csv"]) {
    const f=fixture();f.snapshot.mode=mode;
    assert.equal(enforceDisplayLease(f.snapshot,f.actions,start+8*86400000),null);
    assert.deepEqual(f.events,[]);
  }
});
test("pending network request is never overwritten by timer",()=>{
  const f=fixture();f.snapshot.loading=true;
  assert.equal(enforceDisplayLease(f.snapshot,f.actions,start+8*86400000),null);
  assert.deepEqual(f.events,[]);
});
test("spot-only remains visible until quote expires",()=>{
  const f=fixture();
  f.snapshot.mode="spot-only";f.snapshot.series=null;f.snapshot.historyLatestDate=null;
  assert.equal(enforceDisplayLease(f.snapshot,f.actions,start).state,"spot-only");
  assert.deepEqual(f.events,[]);
  enforceDisplayLease(f.snapshot,f.actions,start+16*60000);
  assert.deepEqual(f.events,["quote","state:unavailable"]);
});
test("history-only remains until history expires",()=>{
  const f=fixture();
  f.snapshot.mode="history-only";f.snapshot.quote=null;f.snapshot.quoteUpdated=null;
  assert.equal(enforceDisplayLease(f.snapshot,f.actions,start).state,"history-only");
  assert.deepEqual(f.events,[]);
});

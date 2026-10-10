import test from "node:test";
import assert from "node:assert/strict";
import {forecast,normalize,predict,tradingDate} from "../forecast.mjs";

function data(n=260,flat=false){
  return Array.from({length:n},(_,i)=>({
    date:new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10),
    price:flat?2500:2500+i*0.8+3*Math.sin(i*1.7)
  }));
}
test("sort and deduplicate UTC dates without inventing prices",()=>{
  assert.deepEqual(normalize([{date:"2026-01-02",price:100},{date:"bad",price:500},{date:"2026-01-01",price:90},{t:"2026-01-02T23:00:00Z",price:110}]),
  [{date:"2026-01-01",price:90},{date:"2026-01-02",price:110}]);
});
test("naive baseline equals latest known price for all supported horizons",()=>{
  const prices=data(100).map(p=>p.price);
  for(const h of [1,7,30])assert.equal(predict(prices,h,"persistence"),prices.at(-1));
});
test("predictions cannot see price observations after origin",()=>{
  const prices=data(130).map(p=>p.price),old=prices.slice(0,100);
  const tampered=old.concat(Array(50).fill(1e7));
  for(const model of ["persistence","momentum","mean_reversion"])
    assert.equal(predict(old,7,model),predict(tampered.slice(0,100),7,model));
});
test("chronological audits exist for all three horizons",()=>{
  for(const h of [1,7,30]){
    const r=forecast(data(),h);
    assert.ok(r.point>0&&r.lower>0&&r.upper>=r.point);
    assert.ok(r.audit.n>=10&&Number.isFinite(r.audit.mae));
    assert.ok(r.auditedFrom<r.latest.date);
    assert.ok(r.coverage>=0&&r.coverage<=100);
  }
});
test("flat prices should not manufacture performance gains",()=>{
  const r=forecast(data(250,true),7);
  assert.equal(r.model,"persistence");
  assert.equal(r.audit.mae,0);
  assert.equal(r.point,2500);
  assert.equal(r.beat,false);
});
test("invalid forecasts fail closed",()=>{
  assert.throws(()=>forecast(data(20),7));
  assert.throws(()=>forecast(data(),5));
  assert.throws(()=>predict(Array(60).fill(2500),3,"fake"));
});
test("session dates skip weekends in illustrative calendar",()=>{
  assert.equal(tradingDate("2026-10-09",1),"2026-10-12");
});
import test from 'node:test';
import assert from 'node:assert/strict';
import {forecast,predict} from '../forecast.mjs';
import {features} from '../models.mjs';
import {prepareProviderHistory,prepareCsvHistory,validatedSpot,crossCheck,UNIT} from '../data.mjs';
import {issueReceipt,settleReceipt,verifyReceipt} from '../journal.mjs';
const data=(n=360)=>Array.from({length:n},(_,i)=>({date:new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10),price:2500+i+20*Math.sin(i*.3)}));
const asOf='2026-01-01T12:00:00Z';

test('audit outcomes cannot influence model choice or calibration band',()=>{
  const raw=data(),a=forecast(raw,7,{asOf}),changed=raw.map((r,i)=>i>=a.split.auditStart?{...r,price:r.price*(1+(i%2)*.15)}:r);
  const b=forecast(changed,7,{asOf});
  assert.equal(a.model,b.model);assert.equal(a.band,b.band);assert.deepEqual(a.candidates,b.candidates);
  assert.notEqual(a.audit.mae,b.audit.mae);
});
test('calibration targets and model selection targets are disjoint',()=>{
  for(const h of [1,7,30]){
    const raw=data(),r=forecast(raw,h,{asOf,includeRows:true});
    assert.ok(r.rows.calibration.at(-1).targetDate<r.auditedFrom);
    assert.ok(raw[r.split.selectionEnd-1].date<r.rows.calibration[0].targetDate);
    assert.equal(r.split.purgedOriginsPerBoundary,h-1);
    assert.equal(r.disjoint.candidate.n,Math.ceil(r.audit.n/h));
  }
});
test('daily and weekdays cadence lead to different explicit target dates',()=>{
  const raw=data(282); // Friday 2025-10-09? use actual last day below
  const daily=forecast(raw,7,{asOf});assert.equal(daily.calendar,'daily');
  const work=data(360).filter(r=>![0,6].includes(new Date(r.date+'T12:00:00Z').getUTCDay()));
  const result=forecast(work,7,{asOf});assert.equal(result.calendar,'weekdays');
  assert.ok((Date.parse(result.targetDate)-Date.parse(result.latest.date))/86400000>=9);
});
test('gaps cannot manufacture a calendar target; malformed CSV fails',()=>{
  const r=forecast(data().filter((_,i)=>i!==250),7,{asOf});
  assert.equal(r.calendar,'observations');assert.equal(r.targetDate,null);
  assert.throws(()=>forecast(data().filter((_,i)=>i<200||i>220),7,{asOf}),/Missing closes/);
  assert.throws(()=>prepareCsvHistory('date,price\n2025-01-01,2500\n2025-01-02,bad',asOf),/Invalid close/);
  assert.throws(()=>prepareCsvHistory('date,price\n2025-01-01,2500,extra',asOf),/Malformed/);
});
test('coarse daily provider feed is rejected despite its grain label',()=>{
  const points=data(500).filter((_,i)=>i%3===0);
  assert.throws(()=>prepareProviderHistory({metal:'XAU',grain:'daily',unit:UNIT,points,attribution:'provider'},'2026-05-16T12:00:00Z'),/downsampled/);
});
test('provider must declare daily gold USD/troy-ounce data and attribution',()=>{
  const payload={metal:'XAU',grain:'daily',unit:UNIT,points:data(),attribution:'Data by Standard Bullion'};
  const recent='2025-12-27T12:00:00Z';
  assert.equal(prepareProviderHistory(payload,recent).calendar,'daily');
  for(const changed of [{metal:'XAG'},{unit:'USD per gram'},{grain:'monthly'},{attribution:''}])
    assert.throws(()=>prepareProviderHistory({...payload,...changed},recent));
});
test('correct UTC quote timestamps pass; stale, crossed and impossible quotes fail',()=>{
  const now=Date.parse(asOf),base={unit:UNIT,updated:asOf,metals:[{symbol:'XAU',ask:2501,bid:2499}]};
  assert.equal(validatedSpot(base,now).ask,2501);
  assert.equal(validatedSpot({...base,updated:'2026-01-01T12:00:00.123Z'},now).bid,2499);
  for(const updated of ['2026-01-01T11:00:00Z','2026-01-02T12:00:00Z','2026-02-30T12:00:00Z','2026-01-01T24:00:00Z','2026-01-01T12:00:00'])
    assert.throws(()=>validatedSpot({...base,updated},now));
  assert.throws(()=>validatedSpot({...base,metals:[{symbol:'XAU',ask:2499,bid:2501}]},now));
  const primary=validatedSpot(base,now);
  assert.equal(crossCheck(primary,{symbol:'XAU',price:2500,updatedAt:asOf},now).status,'consistent_indicative_quotes');
  assert.equal(crossCheck(primary,{symbol:'XAU',price:3000,updatedAt:asOf},now).status,'price_divergence');
});
test('Ridge fits only matured labels and remains finite for flat/scaled inputs',()=>{
  const prices=data(260).map(r=>r.price);
  assert.deepEqual(features(prices,150),features(prices.slice(0,151),150));
  for(const h of [1,7,30]){
    const point=predict(prices,h,'ridge');assert.ok(Number.isFinite(point)&&point>0);
    assert.ok(Math.abs(predict(prices.map(p=>p*10),h,'ridge')/10-point)<1e-5);
    assert.equal(predict(Array(260).fill(2500),h,'ridge'),2500);
  }
});
test('prospective receipt is immutable, pending until exact target close matures',()=>{
  const raw=data(260),issuedAt='2025-09-18T12:00:00Z';
  const receipt=issueReceipt(raw,1,{issuedAt,source:'test',codeCommit:'a'.repeat(40),sourceManifest:{receivedAt:'2025-09-18T11:59:00Z'}});
  assert.equal(verifyReceipt(receipt),true);
  assert.equal(settleReceipt(receipt,raw,{asOf:'2025-09-19T12:00:00Z'}).status,'pending');
  assert.equal(settleReceipt(receipt,data(261),{asOf:'2025-09-19T12:00:00Z'}).status,'matured');
  assert.throws(()=>verifyReceipt({...receipt,point:receipt.point+1}),/integrity/);
  const revised=data(261);revised[10].price+=1;
  assert.throws(()=>settleReceipt(receipt,revised,{asOf:'2025-09-19T12:00:00Z'}),/vintage/);
  const shifted=[...raw,...data(263).slice(261)];
  assert.throws(()=>settleReceipt(receipt,shifted,{asOf:'2025-09-21T12:00:00Z'}),/Target close missing/);
});
test('provisional same-day price cannot enter the committed receipt vintage',()=>{
  const rows=data(260),issuedAt='2025-09-18T12:00:00Z';
  const receipt=issueReceipt([...rows,{date:'2025-09-18',price:1e7}],7,{issuedAt,source:'test',codeCommit:'a'.repeat(40),sourceManifest:{receivedAt:'2025-09-18T11:59:00Z'}});
  assert.equal(receipt.historyLength,260);assert.equal(receipt.originDate,'2025-09-17');
});

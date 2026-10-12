import test from 'node:test';
import assert from 'node:assert/strict';
import {convertOneMinuteOHLCV} from './gold-site-ohlcv-adapter.mjs';
import {parsePriceCSV,evaluateSeries,HORIZON_MS} from './gold-site-offline-eval.mjs';
const head='datetime,open,high,low,close,volume';
const row=(ts,o=4100,h=4102,l=4098,c=4101,v=120)=>[ts,o,h,l,c,v].join(',');
const text=(...rows)=>[head,...rows].join('\n');
test('bar OPEN timestamp cannot be used to predict with that bar CLOSE',()=>{
 const csv=convertOneMinuteOHLCV(text(row('2026-09-01T00:00:00+00:00')));
 const [r]=parsePriceCSV(csv);
 assert.equal(new Date(r.t).toISOString(),'2026-09-01T00:01:00.000Z');
 assert.equal(r.price,4101);
 assert.equal(r.source,'getdata-finance-broker-cfd-1m-close');
});
test('strict source schema, bar ordering, and candle geometry',()=>{
 assert.throws(()=>convertOneMinuteOHLCV('timestamp,price\n1,2'),/header/);
 assert.throws(()=>convertOneMinuteOHLCV(text(row('2026-09-01T00:00:00+00:00'),row('2026-09-01T00:00:00+00:00'))),/Duplicate/);
 assert.throws(()=>convertOneMinuteOHLCV(text(row('2026-09-01T00:00:00+00:00',4100,4099,4098,4101))),/Invalid OHLCV/);
 assert.throws(()=>convertOneMinuteOHLCV(text(row('2026-09-01T00:00:00+00:00',4100,4102,4098,4103))),/Invalid OHLCV/);
 assert.throws(()=>convertOneMinuteOHLCV(text(row('2026-09-01T00:00:30+00:00'))),/minute-aligned/);
 assert.throws(()=>convertOneMinuteOHLCV(text(row('2026-02-30T00:00:00+00:00'))),/Invalid bar/);
});
test('missing session minutes stay missing; never forward-fill',()=>{
 const csv=convertOneMinuteOHLCV(text(row('2026-09-01T00:00:00+00:00'),row('2026-09-01T02:00:00+00:00')));
 const rs=parsePriceCSV(csv);
 assert.equal(rs.length,2);assert.equal(rs[1].t-rs[0].t,120*60_000);
 const e=evaluateSeries(rs,{holdoutStartMs:rs[0].t,strideMs:HORIZON_MS});
 assert.equal(e.evaluated,0);
});
test('adapter accepts Z and fractional zero millisecond UTC timestamps',()=>{
 const csv=convertOneMinuteOHLCV(text(row('2026-09-01T00:00:00.000Z')));
 assert.equal(parsePriceCSV(csv).length,1);
});

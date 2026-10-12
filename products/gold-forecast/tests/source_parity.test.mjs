import test from 'node:test';
import assert from 'node:assert/strict';
import {parseDailyCloseCsv,compareDailyCloses} from '../source_parity.mjs';
const make=(name,rows)=>parseDailyCloseCsv('Date,Close\n'+rows.map(([d,p])=>`${d},${p}`).join('\n'),{sourceId:name});
const dates=['2026-10-06','2026-10-07','2026-10-08','2026-10-09'];
const rows=dates.map((d,i)=>[d,4100+i*2]);
test('identical independently named CSVs screen without claiming skill',()=>{
  const r=compareDailyCloses(make('A',rows),make('B',rows),{minOverlap:3});
  assert.equal(r.status,'screened-within-threshold');
  assert.equal(r.matchedDates,4);assert.equal(r.gapPct.max,0);assert.match(r.warning,/not proof/);
});
test('large one-day divergence is flagged, not averaged away',()=>{
  const other=rows.map(([d,p],i)=>[d,i===2?p*1.12:p]);
  const r=compareDailyCloses(make('A',rows),make('B',other),{minOverlap:3,maxGapPct:1});
  assert.equal(r.status,'requires-review');assert.equal(r.flaggedCount,1);
  assert.equal(r.flaggedExamples[0].date,dates[2]);assert.ok(r.gapPct.max>10);
});
test('non-overlap cannot be misrepresented as agreement',()=>{
  const r=compareDailyCloses(make('A',rows),make('B',[['2026-10-09',4106],['2026-10-12',4107]]),{minOverlap:2});
  assert.equal(r.status,'insufficient-overlap');assert.equal(r.matchedDates,1);
  assert.equal(r.onlySourceA.count,3);assert.equal(r.onlySourceB.count,1);
});
test('reject duplicate, unsorted, invalid date, blank price and unsupported unit',()=>{
  assert.throws(()=>make('A',[rows[0],rows[0]]),/strictly increasing/);
  assert.throws(()=>make('A',[rows[1],rows[0]]),/strictly increasing/);
  assert.throws(()=>make('A',[['2026-02-30',100]]),/Invalid date/);
  assert.throws(()=>parseDailyCloseCsv('Date,Close\n2026-10-09,', {sourceId:'A'}),/Invalid close/);
  assert.throws(()=>parseDailyCloseCsv('Date,Close\n2026-10-09,1',{sourceId:'A',unit:'USD per gram'}),/Only XAU/);
});
test('BOM, column order and positive scientific notation supported',()=>{
  const a=parseDailyCloseCsv('\uFEFFClose,Date\n4.1e3,2026-10-09',{sourceId:'A'});
  assert.equal(a.rows[0].price,4100);
});
test('programmatic rows and same source ID cannot bypass validation',()=>{
  const a=make('A',rows),b=make('B',rows);
  assert.throws(()=>compareDailyCloses(a,{...b,rows:[b.rows[1],b.rows[0]]}),/Invalid or unsorted/);
  assert.throws(()=>compareDailyCloses(a,{...b,sourceId:'A'}),/distinct named/);
  assert.throws(()=>compareDailyCloses(a,b,{minOverlap:1}),/Invalid minOverlap/);
});

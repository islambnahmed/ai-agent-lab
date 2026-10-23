/** Run: node --test experiments/khepri/exp400/integration_production.test.mjs */
import test from 'node:test';
import assert from 'node:assert/strict';
import {prepareProviderHistory,UNIT} from '../../../products/gold-forecast/data.mjs';
import {cadenceAudit,makeDates} from '../exp399/cadence_window.mjs';
import {weekdayCoverage} from './weekday_coverage.mjs';
function fixture(gaps){
  const dates=makeDates('2025-01-01',gaps);
  const asOf=new Date(Date.parse(dates.at(-1)+'T00:00:00Z')+36*3600000).toISOString();
  return {asOf,payload:{metal:'XAU',unit:UNIT,grain:'daily',attribution:'synthetic integration fixture',
    source:'fixture',points:dates.map((date,i)=>({date,price:2500+i/10}))}};
}
test('actual provider validator accepts alternating 1/3-day claimed-daily series',()=>{
  const {payload,asOf}=fixture(Array.from({length:190},(_,i)=>i%2?3:1));
  const result=prepareProviderHistory(payload,asOf);
  assert.equal(result.calendar,'observations');
  assert.equal(result.series.length,191);
  assert.equal(cadenceAudit(result.series).accepted,true);
  assert.equal(weekdayCoverage(result.series).accepted,false);
});
test('new coverage audit does not replace the production gate or modify its return value',()=>{
  const {payload,asOf}=fixture(Array(190).fill(1));
  const result=prepareProviderHistory(payload,asOf);
  assert.equal(result.calendar,'daily');
  assert.equal(weekdayCoverage(result.series).accepted,true);
});

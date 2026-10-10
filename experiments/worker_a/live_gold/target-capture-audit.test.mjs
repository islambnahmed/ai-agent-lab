import test from 'node:test';
import assert from 'node:assert/strict';
import {walkForwardBenchmark} from './walkforward-benchmark.mjs';
const BASE=Date.parse('2026-01-01T00:00:00Z');
const MIN=60_000;
const iso=t=>new Date(t).toISOString().replace('.000Z','Z');
const obs=(minute,price,delayMs=30_000)=>({updatedAt:iso(BASE+minute*MIN),capturedAt:iso(BASE+minute*MIN+delayMs),price});
const regular=()=>[0,60,120,180,240,300,360].map((minute,i)=>obs(minute,2000+i));

test('late capture after provider timestamp cannot be scored as timely outcome',()=>{
 const rows=regular();rows[3]=obs(180,2003,2*60*MIN);
 const result=walkForwardBenchmark(rows);
 assert(result.skipped.targetCaptureLate>=1);
 assert(!result.forecasts.some(f=>f.issuedAt===rows[2].capturedAt && f.targetAt===rows[3].updatedAt));
});
test('explicit one-hour capture window is distinct from default five minutes',()=>{
 const rows=regular();rows[3]=obs(180,2003,30*MIN);
 const strict=walkForwardBenchmark(rows);
 const loose=walkForwardBenchmark(rows,{maxTargetCaptureDelayMs:60*MIN});
 assert(strict.skipped.targetCaptureLate>=1);
 assert(loose.forecasts.some(f=>f.issuedAt===rows[2].capturedAt && f.targetAt===rows[3].updatedAt));
});
test('five-minute capture delay boundary is accepted',()=>{
 const rows=regular();rows[3]=obs(180,2003,5*MIN);
 const result=walkForwardBenchmark(rows);
 assert(result.forecasts.some(f=>f.issuedAt===rows[2].capturedAt && f.targetCaptureDelayMs===5*MIN));
});
test('one millisecond over capture delay boundary is rejected',()=>{
 const rows=regular();rows[3]=obs(180,2003,5*MIN+1);
 const result=walkForwardBenchmark(rows);
 assert(result.skipped.targetCaptureLate>=1);
 assert(!result.forecasts.some(f=>f.issuedAt===rows[2].capturedAt && f.targetAt===rows[3].updatedAt));
});
test('does not cherry-pick second timely provider observation after earliest is captured late',()=>{
 const rows=[obs(0,2000),obs(60,2001),obs(120,2002),obs(184,2003,6*MIN),obs(185,2004),obs(244,2005),obs(304,2006)];
 const result=walkForwardBenchmark(rows,{targetToleranceMs:5*MIN});
 assert(result.skipped.targetCaptureLate>=1);
 assert(!result.forecasts.some(f=>f.issuedAt===rows[2].capturedAt));
});
test('provider target lag and capture lag are separate audit fields',()=>{
 const rows=[obs(0,2000),obs(60,2001),obs(120,2002),obs(184,2003,2*MIN),obs(244,2004),obs(304,2005)];
 const result=walkForwardBenchmark(rows,{targetToleranceMs:5*MIN});
 const f=result.forecasts.find(f=>f.issuedAt===rows[2].capturedAt);
 assert(f);
 assert.equal(f.targetLagMs,4*MIN);
 assert.equal(f.targetCaptureDelayMs,2*MIN);
});
test('capture delay configuration is bounded, integral, and nonnegative',()=>{
 for(const value of [-1,0.5,NaN,Infinity,60*MIN+1]) assert.throws(()=>walkForwardBenchmark(regular(),{maxTargetCaptureDelayMs:value}));
});
test('input records are unchanged and replay is deterministic',()=>{
 const rows=regular();rows[3]=obs(180,2003,12*MIN);
 const before=JSON.stringify(rows);
 assert.deepEqual(walkForwardBenchmark(rows),walkForwardBenchmark(rows));
 assert.equal(JSON.stringify(rows),before);
});

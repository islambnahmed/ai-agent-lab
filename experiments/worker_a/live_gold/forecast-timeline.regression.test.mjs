import test from 'node:test';
import assert from 'node:assert/strict';
import {evaluateForecastTimeline} from './forecast-timeline.mjs';

const quote = (updatedAt, capturedAt, price=4200) => ({symbol:'XAU',currency:'USD',updatedAt,capturedAt,price});
const forecast = {
  createdAt:'2026-10-10T12:00:00Z',
  targetAt:'2026-10-10T13:00:00Z',
  trainedThrough:'2026-10-10T11:59:00Z',
  predictedUsd:4201,
  inputQuote:quote('2026-10-10T11:59:00Z','2026-10-10T11:59:30Z')
};

test('24-hour-late capture cannot be scored as timely target', () => {
  assert.throws(() => evaluateForecastTimeline(forecast,
    quote('2026-10-10T13:00:00Z','2026-10-11T13:00:00Z')), /capture delay/);
});
test('stale input cannot be scored as valid forecast input', () => {
  const bad = {...forecast,inputQuote:quote('2026-10-10T10:00:00Z','2026-10-10T11:59:30Z')};
  assert.throws(() => evaluateForecastTimeline(bad), /input quote age/);
});
test('training cutoff must not exceed latest input provider time', () => {
  const bad = {...forecast,trainedThrough:'2026-10-10T11:59:59Z'};
  assert.throws(() => evaluateForecastTimeline(bad), /training cutoff after input/);
});
test('valid outcome includes separately measured provider lag and capture delay', () => {
  const r = evaluateForecastTimeline(forecast,
    quote('2026-10-10T13:01:00Z','2026-10-10T13:02:00Z',4203));
  assert.equal(r.status,'verified');
  assert.equal(r.observationLagMs,60_000);
  assert.equal(r.targetCaptureDelayMs,60_000);
  assert.equal(r.absoluteErrorUsd,2);
});
test('capture-delay boundary exactly five minutes accepted; +1ms rejected', () => {
  const t = Date.parse('2026-10-10T13:00:00Z'), iso = ms => new Date(ms).toISOString();
  assert.equal(evaluateForecastTimeline(forecast,quote(iso(t),iso(t+300_000))).status,'verified');
  assert.throws(() => evaluateForecastTimeline(forecast,quote(iso(t),iso(t+300_001))),/capture delay/);
});
test('input-age boundary exactly ten minutes accepted; +1ms rejected', () => {
  const t = Date.parse(forecast.createdAt), iso = ms => new Date(ms).toISOString();
  const good = {...forecast,trainedThrough:iso(t-600_000),
    inputQuote:quote(iso(t-600_000),iso(t-30_000))};
  assert.equal(evaluateForecastTimeline(good).status,'pending');
  const bad = {...good,trainedThrough:iso(t-600_001),
    inputQuote:quote(iso(t-600_001),iso(t-30_000))};
  assert.throws(() => evaluateForecastTimeline(bad),/input quote age/);
});
test('invalid delay/age options fail closed', () => {
  for (const bad of [-1,0.5,NaN,Infinity,3_600_001]) {
    assert.throws(() => evaluateForecastTimeline(forecast,null,{maxTargetCaptureDelayMs:bad}),/invalid/);
    assert.throws(() => evaluateForecastTimeline(forecast,null,{maxInputQuoteAgeMs:bad}),/invalid/);
  }
});
test('observation before target is rejected', () => {
  assert.throws(() => evaluateForecastTimeline(forecast,
    quote('2026-10-10T12:59:59Z','2026-10-10T13:00:00Z')), /predates target/);
});

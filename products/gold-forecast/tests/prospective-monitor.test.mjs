import test from 'node:test';
import assert from 'node:assert/strict';
import {monitorProspective} from '../prospective-monitor.mjs';

const day = i => new Date(Date.UTC(2026, 0, 1 + i)).toISOString().slice(0, 10);
const matured = (i, {horizon = 7, modelAbsError = 2, baselineAbsError = 1, covered = false} = {}) =>
  ({id: `receipt-${horizon}-${i}`, horizon, status: 'matured', targetDate: day(i),
    modelAbsError, baselineAbsError, covered});
const opts = {minMatured: 3, window: 4, degradeRatio: 1.1, maxWinRate: 0.4};

test('insufficient outcomes never raise degradation, even for large errors', () => {
  const r = monitorProspective([matured(0), matured(1)], 7, opts);
  assert.equal(r.status, 'insufficient_prospective_outcomes');
  assert.equal(r.evaluated, 2);
});

test('descriptive degradation flag requires adequate matured observations', () => {
  const r = monitorProspective([matured(0), matured(1), matured(2)], 7, opts);
  assert.equal(r.status, 'descriptive_degradation_flag');
  assert.equal(r.maeRatio, 2);
  assert.equal(r.winRate, 0);
  assert.match(r.caution, /Never automatically switch models/);
});

test('a better candidate does not trigger a degradation flag', () => {
  const r = monitorProspective([0, 1, 2, 3].map(i => matured(i, {modelAbsError: 0.5})), 7, opts);
  assert.equal(r.status, 'no_degradation_flag');
  assert.equal(r.winRate, 1);
});

test('only the latest window contributes, regardless of input order', () => {
  const rows = [0, 1, 2].map(i => matured(i, {modelAbsError: 100})).concat(
    [3, 4, 5, 6].map(i => matured(i, {modelAbsError: 0.5, covered: true})));
  const a = monitorProspective(rows, 7, opts);
  const b = monitorProspective([...rows].reverse(), 7, opts);
  assert.deepEqual(a, b);
  assert.equal(a.status, 'no_degradation_flag');
  assert.equal(a.evaluated, 4);
  assert.equal(a.from, day(3));
  assert.equal(a.intervalCoverage, 1);
});

test('horizons are never pooled; pending and quarantined are excluded', () => {
  const rows = [matured(0), matured(1), matured(2, {horizon: 30}),
    {id: 'pending', horizon: 7, status: 'pending'},
    {id: 'quarantined', horizon: 7, status: 'quarantined'},
    {id: 'unknown-horizon-quarantine', status: 'quarantined'}];
  const r = monitorProspective(rows, 7, opts);
  assert.equal(r.totalMatured, 2);
  assert.equal(r.pending, 1);
  assert.equal(r.quarantined, 1);
  assert.equal(r.unattributedQuarantines, 1);
  assert.equal(r.status, 'insufficient_prospective_outcomes');
});

test('zero-error baseline is handled without dividing by zero', () => {
  const rows = [0, 1, 2].map(i => matured(i, {baselineAbsError: 0, modelAbsError: 0.1}));
  const r = monitorProspective(rows, 7, opts);
  assert.equal(r.maeRatio, null);
  assert.equal(r.status, 'descriptive_degradation_flag');
});

test('duplicate receipt ids are rejected, including across horizons', () => {
  const rows = [matured(0), {...matured(1, {horizon: 30}), id: 'receipt-7-0'}];
  assert.throws(() => monitorProspective(rows, 7, opts), /Duplicate receipt id/);
});

test('duplicate target dates for the same horizon fail closed', () => {
  assert.throws(() => monitorProspective([matured(0), {...matured(0), id: 'different'}], 7, opts), /Duplicate target date/);
});

test('invalid matured outcomes fail closed instead of contaminating MAE', () => {
  for (const patch of [
    {modelAbsError: -1}, {modelAbsError: Infinity}, {baselineAbsError: NaN},
    {targetDate: '2026-02-30'}, {covered: 'true'}
  ]) {
    assert.throws(() => monitorProspective([{...matured(0), ...patch}], 7, opts), /Invalid matured settlement/);
  }
});

test('invalid horizons and monitoring policies fail closed', () => {
  assert.throws(() => monitorProspective([], 2), /Unsupported horizon/);
  for (const options of [{minMatured: 1}, {window: 1}, {degradeRatio: 1}, {maxWinRate: 2}])
    assert.throws(() => monitorProspective([], 7, options), /Invalid monitoring policy/);
});

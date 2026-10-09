import test from 'node:test';
import assert from 'node:assert/strict';
import {evaluateDisplayLease} from '../freshness_lease.mjs';
const now=Date.parse('2026-10-09T16:00:00Z');
test('quote expires independently of still-current history',()=>{
  const a=evaluateDisplayLease({nowMs:now,quoteUpdated:'2026-10-09T15:46:00Z',historyLatestDate:'2026-10-09'});
  const b=evaluateDisplayLease({nowMs:now+120000,quoteUpdated:'2026-10-09T15:46:00Z',historyLatestDate:'2026-10-09'});
  assert.equal(a.state,'live');assert.equal(b.state,'history-only');
});
test('history expires after configured age',()=>{
  const x=evaluateDisplayLease({nowMs:now,historyLatestDate:'2026-09-30'});
  assert.equal(x.state,'unavailable');
});
